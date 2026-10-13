# 8. Dependências, bibliotecas e serviços

Versões fixadas em `backend/requirements.txt`, `frontend/package-lock.json` e `docker-compose.yml`
(levantamento de outubro de 2026).

## 8.1 Backend (Python 3.12)

| Biblioteca | Versão | Licença | Uso no projeto | Site |
|---|---|---|---|---|
| FastAPI | 0.143.0 | MIT | Framework da API REST, validação e OpenAPI | https://fastapi.tiangolo.com |
| Uvicorn | 0.54.0 | BSD-3-Clause | Servidor ASGI | https://www.uvicorn.org |
| Pydantic | 2.14.1 | MIT | Modelos de dados e validação (DTOs) | https://docs.pydantic.dev |
| pydantic-settings | 2.15.0 | MIT | Configuração por variáveis de ambiente | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| python-multipart | 0.0.32 | Apache-2.0 | Upload de arquivos (multipart/form-data) | https://github.com/Kludex/python-multipart |
| SQLAlchemy | 2.1.4 | MIT | ORM, repositórios e unidade de trabalho | https://www.sqlalchemy.org |
| psycopg | 3.3.6 | LGPL-3.0 | Driver PostgreSQL | https://www.psycopg.org |
| qdrant-client | 1.19.1 | Apache-2.0 | Cliente do banco vetorial Qdrant | https://github.com/qdrant/qdrant-client |
| PyJWT | 2.15.1 | MIT | Tokens de acesso JWT (RFC 7519) | https://pyjwt.readthedocs.io |
| bcrypt | 5.0.0 | Apache-2.0 | Hash de senhas | https://github.com/pyca/bcrypt |
| google-genai | 2.29.0 | Apache-2.0 | SDK do Gemini: geração de texto, listagem de modelos e embeddings | https://googleapis.github.io/python-genai/ |
| openai | 3.29.0 | Apache-2.0 | SDK da OpenAI (Responses API e listagem de modelos) | https://github.com/openai/openai-python |
| cohere | 7.2.0 | MIT | SDK da Cohere (rerank) | https://github.com/cohere-ai/cohere-python |
| tenacity | 9.1.4 | Apache-2.0 | Novas tentativas com espera exponencial | https://tenacity.readthedocs.io |
| PyMuPDF | 1.28.2 | AGPL-3.0 ou comercial | Leitura de PDF, análise de páginas e renderização para OCR | https://pymupdf.readthedocs.io |
| pytesseract | 0.3.13 | Apache-2.0 | Interface Python do Tesseract | https://github.com/madmaze/pytesseract |
| Pillow | 12.3.0 | MIT-CMU | Processamento de imagens para OCR | https://python-pillow.org |
| python-docx | 1.2.0 | MIT | Leitura de .docx | https://python-docx.readthedocs.io |
| python-pptx | 1.0.2 | MIT | Leitura de .pptx | https://python-pptx.readthedocs.io |
| pandas | 3.0.6 | BSD-3-Clause | Leitura de planilhas e CSV | https://pandas.pydata.org |
| openpyxl | 3.1.5 | MIT | Motor de leitura .xlsx | https://openpyxl.readthedocs.io |
| xlrd | 2.0.2 | BSD | Motor de leitura .xls | https://github.com/python-excel/xlrd |
| odfpy | 1.4.1 | Apache-2.0 / GPL / LGPL | Motor de leitura .ods | https://github.com/eea/odfpy |
| charset-normalizer | 3.5.2 | MIT | Detecção de codificação de arquivos de texto | https://github.com/jawah/charset_normalizer |
| pytest | 9.1.1 | MIT | Testes automatizados (desenvolvimento) | https://docs.pytest.org |

> **Atenção à licença do PyMuPDF (AGPL-3.0).** Em uso acadêmico com código-fonte aberto não há impedimento. Para
> distribuição comercial com código fechado é necessária a licença comercial da Artifex ou a troca da biblioteca.

## 8.2 Frontend

| Biblioteca | Versão | Licença | Uso no projeto | Site |
|---|---|---|---|---|
| Angular (`@angular/*`) | 22.2.2 | MIT | Framework da SPA (componentes standalone, signals, roteamento, HTTP, formulários) | https://angular.dev |
| Angular CLI / `@angular/build` | 22.2.2 | MIT | Build (esbuild/Vite) | https://angular.dev/tools/cli |
| TypeScript | 6.0.3 | Apache-2.0 | Linguagem | https://www.typescriptlang.org |
| RxJS | 7.8.2 | Apache-2.0 | Programação reativa (HttpClient, eventos de upload) | https://rxjs.dev |
| tslib | 2.8.1 | 0BSD | Auxiliares do compilador TypeScript | https://github.com/microsoft/tslib |
| marked | 18.1.1 | MIT | Conversão de Markdown das respostas em HTML | https://marked.js.org |
| DOMPurify | 3.4.17 | MPL-2.0 ou Apache-2.0 | Sanitização do HTML (proteção contra XSS) | https://github.com/cure53/DOMPurify |
| Prettier | 3.9.10 | MIT | Formatação de código (desenvolvimento) | https://prettier.io |
| Fonte Inter | — | SIL OFL 1.1 | Tipografia (Google Fonts) | https://rsms.me/inter/ |
| Ícones | — | ISC | Traçados no estilo da coleção Lucide | https://lucide.dev |

## 8.3 Infraestrutura e serviços

| Componente | Versão | Licença | Uso |
|---|---|---|---|
| Docker / Docker Compose | 29.x / v5 | Apache-2.0 | Conteinerização e orquestração |
| PostgreSQL | 17.11 (`postgres:17-alpine`) | PostgreSQL License | Banco relacional e fila de jobs |
| Qdrant | 1.19.2 | Apache-2.0 | Banco vetorial (HNSW, cosseno) |
| Nginx | 1.29.8 | BSD-2-Clause | Servidor web e proxy reverso |
| Node.js | 24 (build) | MIT | Build do frontend |
| Python | 3.12.15 | PSF License | Runtime do backend |
| Tesseract OCR | 5.5.0 (`por`, `eng`) | Apache-2.0 | OCR de páginas escaneadas e imagens |
| LibreOffice (headless) | 25.2 | MPL-2.0 | Conversão de .doc, .rtf, .odt, .ppt, .odp |

## 8.4 Modelos e APIs de IA

| Provedor | Modelo | Uso | Documentação |
|---|---|---|---|
| Google | `gemini-3.8-flash` (padrão, configurável) | Geração das respostas, reescrita de perguntas, juiz da avaliação | https://ai.google.dev/gemini-api/docs/models |
| Google | `gemini-embedding-001` (3072 dimensões) | Embeddings de documentos e consultas | https://ai.google.dev/gemini-api/docs/embeddings |
| OpenAI | modelos de chat disponíveis na conta (ex.: família GPT-5) | LLM alternativo selecionável | https://platform.openai.com/docs/models |
| Cohere | `rerank-v4.0-pro` (padrão), `rerank-v4.0-fast`, `rerank-v3.5` | Reordenação dos trechos recuperados | https://docs.cohere.com/docs/rerank |
