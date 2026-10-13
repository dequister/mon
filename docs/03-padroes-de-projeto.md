# 3. Padrões de projeto

Os padrões abaixo seguem os catálogos de Gamma *et al.* (1994) — padrões GoF — e de Fowler (2002) — padrões de
arquitetura de aplicações corporativas —, além da arquitetura hexagonal (Cockburn, 2005) e da Arquitetura
Limpa (Martin, 2017).

## 3.1 Padrões arquiteturais

| Padrão | Onde | Por quê |
|---|---|---|
| **Arquitetura hexagonal (Ports and Adapters)** | `domain/ports.py` (portas) e `infrastructure/` (adaptadores) | Isola as regras de negócio dos provedores externos (Gemini, OpenAI, Cohere, Qdrant, Tesseract). |
| **Camadas (Layered)** | `api` → `services` → `repositories` / `infrastructure` | Separa apresentação, casos de uso e acesso a dados. |
| **Composition Root / Injeção de dependência** | `app/container.py`, `Depends` do FastAPI | Um único ponto monta os objetos; serviços recebem dependências por construtor. |
| **Application Factory** | `create_app()` em `app/main.py` | Cria a aplicação configurada (rotas, tratadores de erro, ciclo de vida). |

## 3.2 Padrões de criação

| Padrão | Onde | Por quê |
|---|---|---|
| **Factory / Registry** | `LoaderFactory` (`infrastructure/loaders/factory.py`) | Escolhe o leitor de arquivo pela extensão; novos formatos entram registrando um loader. |
| **Factory / Registry** | `LLMProviderFactory` (`infrastructure/llm/factory.py`) | Cria o provedor de LLM configurado pelo administrador (Google ou OpenAI). |
| **Builder** | `PromptBuilder` (`services/rag/prompt_builder.py`) | Monta o prompt em partes: persona, regras, contexto numerado e pergunta. |
| **Singleton** | `get_settings()`, `get_vector_store()` com `lru_cache` | Uma instância por processo para configuração e clientes de rede. |

## 3.3 Padrões estruturais

| Padrão | Onde | Por quê |
|---|---|---|
| **Adapter** | `GoogleLLMProvider`, `OpenAILLMProvider`, `QdrantVectorStore`, `CohereReranker`, `TesseractOcrEngine` | Convertem as APIs dos SDKs para as interfaces do domínio. |
| **Adapter (conversão)** | `LibreOfficeConvertingLoader` | Converte `.doc`, `.rtf`, `.odt`, `.ppt` para formatos modernos e delega ao loader correspondente. |
| **Facade** | `RagService` | Expõe `retrieve`, `stream` e `answer`, escondendo o pipeline, o prompt e os provedores. |
| **Null Object** | `PassthroughReranker`, `NullProgressReporter` | Comportamento neutro quando o rerank está desligado ou não há observador de progresso. |
| **DTO** | `api/schemas/*.py` (Pydantic) | Define contratos de entrada e saída da API, desacoplados do ORM. |

## 3.4 Padrões comportamentais

| Padrão | Onde | Por quê |
|---|---|---|
| **Strategy** | `DocumentLoader` (PDF, DOCX, planilhas...), `TextChunker`, `ScanDetector`, `Reranker`, `EmbeddingProvider` | Algoritmos intercambiáveis por tipo de arquivo ou por configuração. |
| **Template Method** | `BaseLoader.load()` | Fluxo fixo (extrair → normalizar → descartar vazios); cada formato implementa só `_extract()`. |
| **Chain of Responsibility / Pipeline** | `RetrievalPipeline` com `QueryRewriteStep`, `VectorSearchStep`, `RerankStep` | Etapas independentes que enriquecem um contexto compartilhado e medem o próprio tempo. |
| **Command** | `JobHandler` e handlers em `workers/handlers.py` | Cada job persistido é um comando executado pelo handler do seu tipo. |
| **Observer** | `ProgressReporter` / `JobProgressReporter` | Serviços longos notificam progresso e log sem conhecer o worker. |

## 3.5 Padrões de acesso a dados (Fowler, 2002)

| Padrão | Onde | Por quê |
|---|---|---|
| **Repository** | `repositories/*.py` (base genérica `SqlAlchemyRepository[T]`) | Encapsula consultas; serviços não escrevem SQL. |
| **Unit of Work** | `Session` do SQLAlchemy; `get_db()` e `session_scope()` | Uma transação por requisição ou por tarefa, com *commit*/*rollback* centralizados. |
| **Service Layer** | `services/*.py` | Define os casos de uso da aplicação sobre o modelo de domínio. |

## 3.6 Frontend (Angular)

| Padrão | Onde | Por quê |
|---|---|---|
| **Facade + Store (estado reativo)** | `ChatStore` com *signals* | Centraliza o estado do chat (conversas, mensagens, streaming) para os componentes. |
| **Interceptor (Chain of Responsibility)** | `authInterceptor` | Anexa o JWT e trata respostas 401 em todas as requisições. |
| **Guard** | `authGuard`, `adminGuard`, `guestGuard` | Protegem rotas por autenticação e papel. |
| **Injeção de dependência** | `inject()` / `providedIn: 'root'` | Serviços únicos (singleton) e testáveis. |
| **Pipe** | `MarkdownPipe`, `FileSizePipe`, `RelativeTimePipe` | Transformações de apresentação reutilizáveis. |
