# 2. Arquitetura

## 2.1 Visão de contêineres

```mermaid
flowchart LR
    U([Usuário]) -->|HTTPS| FE[frontend<br/>Nginx + Angular]
    FE -->|/api REST + SSE| BE[backend<br/>FastAPI]
    BE --> PG[(PostgreSQL<br/>usuários, conversas,<br/>documentos, jobs)]
    BE --> QD[(Qdrant<br/>vetores + metadados)]
    WK[worker<br/>fila de jobs] --> PG
    WK --> QD
    BE -.->|enfileira jobs| PG
    WK --> FS[(Volume de arquivos<br/>/data/uploads)]
    BE --> FS
    WK --> SRC[(Pasta sincronizada<br/>/data/sources)]
    BE --> GEM[[Google Gemini<br/>LLM + embeddings]]
    BE --> OAI[[OpenAI<br/>LLM opcional]]
    BE --> COH[[Cohere<br/>rerank]]
    WK --> GEM
```

| Serviço | Imagem | Responsabilidade |
|---|---|---|
| `frontend` | `nginx:1.29-alpine` (build com `node:24-alpine`) | Servir a SPA Angular e encaminhar `/api` ao backend |
| `backend` | `python:3.12-slim` + Tesseract + LibreOffice | API REST, autenticação, chat com streaming |
| `worker` | mesma imagem do backend | Executar jobs: indexação, sincronização, avaliação |
| `postgres` | `postgres:17-alpine` | Dados relacionais e fila de jobs |
| `qdrant` | `qdrant/qdrant:v1.19.2` | Banco vetorial (HNSW, distância cosseno, 3072 dimensões) |

A fila de jobs usa o próprio PostgreSQL (`SELECT ... FOR UPDATE SKIP LOCKED`), evitando um *broker* adicional
(Redis/RabbitMQ) e mantendo o estado dos jobs consultável pela interface.

## 2.2 Camadas do backend (arquitetura hexagonal)

```mermaid
flowchart TB
    subgraph API["api/ — adaptadores de entrada"]
        R[Routers FastAPI] --> S[Schemas Pydantic / DTOs]
    end
    subgraph APP["services/ — casos de uso"]
        CS[ChatService] --> RS[RagService - Facade]
        RS --> PL[RetrievalPipeline]
        IS[IngestionService]
        DS[DocumentService]
        ES[EvalService]
        JS[JobService]
    end
    subgraph DOM["domain/ — núcleo"]
        P[Ports - interfaces ABC]
        E[Entidades]
    end
    subgraph INF["infrastructure/ — adaptadores de saída"]
        L[Loaders + OCR]
        V[QdrantVectorStore]
        LLM[Google / OpenAI Providers]
        EMB[GoogleEmbeddingProvider]
        RR[CohereReranker]
    end
    subgraph DB["repositories/ + db/"]
        REP[Repositórios SQLAlchemy]
    end
    R --> APP
    APP --> P
    INF -. implementa .-> P
    APP --> REP
    W[workers/ - Command handlers] --> APP
```

| Pasta | Conteúdo |
|---|---|
| `app/core` | Configuração (`pydantic-settings`), segurança (bcrypt, JWT), exceções, logging |
| `app/domain` | Entidades (`DocumentSection`, `Chunk`, `RetrievedChunk`...) e portas (`LLMProvider`, `VectorStore`...) |
| `app/db` | Modelos ORM, sessão e inicialização do banco |
| `app/repositories` | Repositórios por agregado (usuário, conversa, documento, job, avaliação) |
| `app/infrastructure` | Adaptadores: loaders, OCR, chunking, embeddings, LLMs, rerank, Qdrant, armazenamento |
| `app/services` | Casos de uso e pipelines (ingestão, RAG, chat, avaliação, sincronização) |
| `app/workers` | Worker de jobs e handlers por tipo de job |
| `app/api` | Rotas REST, dependências (autenticação) e DTOs |
| `app/container.py` | *Composition root*: monta e injeta os adaptadores |

Os serviços dependem apenas das **portas** do domínio. Trocar o Qdrant por outro banco vetorial ou o Gemini por
outro provedor exige somente um novo adaptador, sem alterar os casos de uso (princípio da inversão de dependência).

## 2.3 Frontend

```
src/app/
├── core/          modelos da API, serviços HTTP, interceptor JWT, guards, ChatStore (estado com signals)
├── shared/        ícones, logo, diálogos, pipes (markdown, datas, tamanhos)
├── layout/        shell (estrutura) e sidebar (conversas + rodapé administrativo)
└── features/
    ├── auth/      login
    ├── chat/      página do chat, caixa de mensagem, card da resposta, painel de fontes
    └── admin/     documentos, jobs, avaliação, modelos e RAG
```

- Componentes *standalone*, *signals* e aplicação sem `zone.js` (*zoneless*).
- Rotas com *lazy loading* e *guards* (`authGuard`, `adminGuard`).
- O chat lê a resposta via `fetch` + `ReadableStream`, interpretando os eventos SSE.

## 2.4 Modelo de dados relacional

```mermaid
erDiagram
    users ||--o{ conversations : possui
    conversations ||--o{ messages : contem
    users ||--o{ documents : envia
    users ||--o{ jobs : cria
    eval_runs ||--o{ eval_results : gera
    eval_cases ||--o{ eval_results : avalia

    users {
        uuid id PK
        string username
        string password_hash
        string role
    }
    conversations {
        uuid id PK
        uuid user_id FK
        string title
        timestamp updated_at
    }
    messages {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        jsonb sources
        jsonb details
        text error
    }
    documents {
        uuid id PK
        string filename
        string sha256
        string status
        int version
        int chunk_count
        int ocr_pages
        jsonb extraction
    }
    jobs {
        uuid id PK
        string type
        string status
        jsonb payload
        float progress
        text log
    }
    app_settings {
        string key PK
        jsonb value
    }
    eval_cases {
        uuid id PK
        text question
        text expected_answer
        jsonb expected_documents
    }
    eval_runs {
        uuid id PK
        string name
        string status
        jsonb config
        jsonb metrics
    }
    eval_results {
        uuid id PK
        uuid run_id FK
        text answer
        jsonb retrieved
        jsonb metrics
    }
```

## 2.5 Modelo de dados vetorial (Qdrant)

Coleção `mon_documents`: vetores de **3072 dimensões**, distância **cosseno**. Cada ponto (chunk) carrega:

| Campo do payload | Descrição | Indexado |
|---|---|---|
| `document_id` | ID do documento no PostgreSQL | sim (keyword) |
| `version` | Versão da indexação | sim (integer) |
| `filename`, `file_type` | Nome e tipo do arquivo | sim (keyword) |
| `chunk_index` | Posição do chunk no documento | — |
| `text` | Texto do chunk (usado no prompt e nas fontes) | — |
| `page`, `sheet`, `heading` | Localização (página/slide, aba, seção) | — |
| `ocr` | Se o texto veio de OCR | — |
| `source`, `sha256`, `indexed_at` | Origem, hash do arquivo e data de indexação | — |

O ID de cada ponto é um UUID v5 determinístico de `documento:versão:chunk`.
