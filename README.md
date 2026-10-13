# Mon — Assistente virtual para consulta de documentos institucionais

O **Mon** é um sistema de *Retrieval-Augmented Generation* (RAG) que permite consultar, em linguagem natural,
documentos do CEFET/RJ: editais, regulamentos, planilhas, apresentações e documentos digitalizados.
Cada resposta traz a seção **"Fontes consultadas"**, com os arquivos, páginas e trechos usados.

Projeto desenvolvido como Trabalho de Conclusão de Curso em Engenharia de Produção.

## Funcionalidades

- **Chat com streaming** e histórico de conversas por usuário (barra lateral).
- **Fontes consultadas** em cada resposta: arquivo, página/aba/slide, relevância, OCR e trecho.
- **Ingestão multiformato**: PDF, DOC, DOCX, ODT, RTF, XLS, XLSX, ODS, CSV, PPT, PPTX, TXT, MD, HTML e imagens.
- **OCR seletivo**: cada página de PDF é analisada; só as escaneadas (ou híbridas) passam pelo Tesseract.
- **Reindexação sem resíduos**: vetores versionados no Qdrant; a versão antiga só é removida após o sucesso da nova.
- **Área administrativa**: upload por arrastar e soltar, jobs de sincronização, avaliação do RAG e seleção de modelos
  (Google Gemini e OpenAI) e parâmetros de recuperação.
- **Avaliação do RAG**: hit rate, MRR, recall, precisão de contexto e LLM como juiz (fidelidade, relevância, correção).

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Frontend | Angular 22, TypeScript, SCSS, Nginx |
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Banco relacional | PostgreSQL 17 |
| Banco vetorial | Qdrant 1.19 |
| LLM | Gemini 3.8 Flash (padrão) ou modelos OpenAI |
| Embeddings | `gemini-embedding-001` (3072 dimensões) |
| Rerank | Cohere `rerank-v4.0-pro` |
| OCR | Tesseract 5 (português + inglês) |
| Infraestrutura | Docker e Docker Compose |

## Como executar

```bash
cp .env.example .env        # preencha GOOGLE_API_KEY, COHERE_API_KEY e, se quiser, OPENAI_API_KEY
docker compose up -d --build
```

Acesse <http://localhost:8080> e entre com **admin / admin**.

Guia completo em [docs/10-execucao.md](docs/10-execucao.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [Visão geral](docs/01-visao-geral.md) | Objetivo, escopo e requisitos |
| [Arquitetura](docs/02-arquitetura.md) | Componentes, camadas, dados e diagramas |
| [Padrões de projeto](docs/03-padroes-de-projeto.md) | Padrões aplicados e onde estão no código |
| [Ingestão e OCR](docs/04-ingestao-e-ocr.md) | Extração, detecção de páginas escaneadas, chunking e reindexação |
| [RAG e chat](docs/05-rag-e-chat.md) | Recuperação, rerank, prompt, streaming e fontes |
| [Avaliação](docs/06-avaliacao.md) | Métricas e metodologia de avaliação |
| [API](docs/07-api.md) | Endpoints REST |
| [Dependências](docs/08-dependencias.md) | Bibliotecas, versões e licenças |
| [Referências](docs/09-referencias.md) | Referências bibliográficas (ABNT) |
| [Execução](docs/10-execucao.md) | Instalação, configuração e testes |

## Estrutura do repositório

```
.
├── backend/            API FastAPI, worker de jobs e testes
├── frontend/           Aplicação Angular (servida pelo Nginx)
├── data/sources/       Pasta sincronizável com a base de arquivos
├── docs/               Documentação do projeto
├── docker-compose.yml  Orquestração dos serviços
└── SYSTEM_PROMPT.md    Persona padrão do assistente
```
