# 10. Instalação, configuração e testes

## 10.1 Pré-requisitos

- Docker Desktop (ou Docker Engine) com Docker Compose v2+;
- chaves de API:
  - **Google AI Studio** (`GOOGLE_API_KEY`): obrigatória, usada no LLM padrão e nos embeddings;
  - **Cohere** (`COHERE_API_KEY`): recomendada, usada no rerank (sem ela a ordem da busca vetorial é mantida);
  - **OpenAI** (`OPENAI_API_KEY`): opcional, habilita os modelos da OpenAI.

## 10.2 Configuração

```bash
cp .env.example .env
```

Edite o `.env` e preencha as chaves. Principais variáveis:

| Variável | Padrão | Descrição |
|---|---|---|
| `GOOGLE_API_KEY` | — | Chave do Gemini (LLM e embeddings) |
| `COHERE_API_KEY` | — | Chave da Cohere (rerank) |
| `OPENAI_API_KEY` | — | Chave da OpenAI (opcional) |
| `JWT_SECRET` | — | Segredo de assinatura dos tokens (use um valor longo e aleatório) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / `admin` | Administrador criado na primeira execução |
| `DEFAULT_LLM_MODEL` | `gemini-3.8-flash` | Modelo inicial (alterável na interface) |
| `DEFAULT_RERANK_MODEL` | `rerank-v4.0-pro` | Modelo de rerank inicial |
| `EMBEDDING_MODEL` / `EMBEDDING_DIMENSIONS` | `gemini-embedding-001` / `3072` | Embeddings (alterar exige recriar a coleção e reindexar) |
| `OCR_LANGUAGES` / `OCR_DPI` | `por+eng` / `300` | Idiomas e resolução do OCR |
| `WORKER_CONCURRENCY` | `2` | Jobs processados em paralelo |
| `APP_PORT` | `8080` | Porta da aplicação |

A persona do assistente vem de `SYSTEM_PROMPT.md` e pode ser editada depois na tela **Modelos e RAG**.

## 10.3 Execução

```bash
docker compose up -d --build
```

| Endereço | Serviço |
|---|---|
| http://localhost:8080 | Aplicação (login `admin` / `admin`) |
| http://localhost:8080/api/docs | Documentação interativa da API |
| http://localhost:6333/dashboard | Painel do Qdrant |

Após alterar o `.env`, recrie os serviços do backend:

```bash
docker compose up -d --force-recreate backend worker
```

Comandos úteis:

```bash
docker compose ps                 # estado dos serviços
docker compose logs -f worker     # acompanhar indexação
docker compose down               # parar (mantém os dados)
docker compose down -v            # parar e APAGAR banco, vetores e uploads
```

## 10.4 Primeiro uso

1. Entre como `admin` / `admin` (troque a senha em produção).
2. Em **Modelos e RAG**, confira se os provedores aparecem como configurados e teste o modelo.
3. Em **Documentos**, arraste os arquivos. Acompanhe a indexação na própria tela ou em **Jobs de sincronização**.
4. Opcional: coloque arquivos em `data/sources/` e clique em **Sincronizar pasta**.
5. Volte ao chat e faça perguntas. Abra as **fontes consultadas** para conferir os trechos.
6. Em **Avaliação do RAG**, gere ou cadastre casos de teste e execute uma avaliação.

## 10.5 Testes automatizados

Testes unitários (chunking, detecção de páginas escaneadas, loaders, métricas, segurança):

```bash
docker compose exec backend pytest -q
```

Teste de integração com PostgreSQL e Qdrant reais e provedores de IA simulados (ingestão, duplicidade,
reindexação versionada sem resíduos, RAG com citações, métricas de avaliação e exclusão):

```bash
docker compose exec -e RUN_INTEGRATION=1 backend pytest -q tests/test_integration.py
```

## 10.6 Desenvolvimento local (opcional)

Backend (Python 3.12, PostgreSQL e Qdrant em execução):

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload       # API em http://localhost:8000
python -m app.worker                # worker em outro terminal
```

Frontend (Node.js 22.22+ ou 24):

```bash
cd frontend
npm install
npm start                           # http://localhost:4200, com proxy para a API em :8000
```

## 10.7 Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| Documento com status "Falhou" e mensagem sobre `GOOGLE_API_KEY` | Chave não configurada | Preencha o `.env`, recrie backend/worker e clique em **Reindexar** |
| Lista de modelos vazia | Chave do provedor ausente ou inválida | Verifique a chave; use o botão **Testar** |
| Respostas sem rerank | `COHERE_API_KEY` ausente ou rerank desligado | Configure a chave ou ative em **Modelos e RAG** |
| Erro de dimensões no Qdrant | Modelo de embedding alterado | `docker compose down -v` (apaga dados) e reindexe |
| `.doc`/`.ppt` não processa | Conversão do LibreOffice falhou | Veja o log do job; salve o arquivo em formato moderno |
