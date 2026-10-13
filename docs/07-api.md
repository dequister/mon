# 7. API REST

Base: `/api`. Documentação interativa (OpenAPI/Swagger) em <http://localhost:8080/api/docs>.
Todas as rotas, exceto login e saúde, exigem `Authorization: Bearer <token>`. Rotas marcadas com **admin**
exigem o papel de administrador.

## Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Recebe `{username, password}` e devolve o token JWT e o usuário |
| GET | `/auth/me` | Dados do usuário autenticado |
| POST | `/auth/change-password` | Troca a senha (`current_password`, `new_password`) |

## Conversas e chat

| Método | Rota | Descrição |
|---|---|---|
| GET | `/conversations` | Conversas do usuário (mais recentes primeiro) |
| POST | `/conversations` | Cria conversa |
| PATCH | `/conversations/{id}` | Renomeia |
| DELETE | `/conversations/{id}` | Exclui conversa e mensagens |
| GET | `/conversations/{id}/messages` | Mensagens com fontes e detalhes |
| POST | `/conversations/{id}/messages` | Envia pergunta; resposta em **SSE** (`start`, `sources`, `delta`, `done`, `error`) |

## Documentos

| Método | Rota | Descrição |
|---|---|---|
| GET | `/documents?q=&status_filter=` | Lista documentos (**admin**) |
| GET | `/documents/stats` | Totais por status, chunks, vetores e extensões suportadas (**admin**) |
| GET | `/documents/names` | Nomes dos arquivos (para a avaliação) (**admin**) |
| POST | `/documents/upload` | Upload multipart (`files`), um ou vários arquivos (**admin**) |
| GET | `/documents/{id}` | Detalhes, incluindo relatório de extração (**admin**) |
| GET | `/documents/{id}/download` | Baixa o arquivo original (usuário autenticado) |
| POST | `/documents/{id}/reindex` | Agenda reindexação (**admin**) |
| DELETE | `/documents/{id}` | Remove documento, arquivo e vetores (**admin**) |

## Jobs (**admin**)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/jobs?status=&type=&limit=` | Lista jobs |
| GET | `/jobs/stats` | Quantidade por status |
| GET | `/jobs/{id}` | Detalhes com log |
| POST | `/jobs/sync-folder` | Agenda sincronização da pasta `data/sources` |
| POST | `/jobs/reindex-all` | Agenda reindexação de todos os documentos |
| POST | `/jobs/{id}/cancel` | Cancela job na fila |
| POST | `/jobs/{id}/retry` | Reexecuta job com falha ou cancelado |

## Administração de modelos e RAG (**admin**)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/admin/settings` | Configurações do RAG |
| PUT | `/admin/settings` | Atualização parcial (modelo, top-k, rerank, chunking, persona...) |
| GET | `/admin/providers` | Provedores e se têm chave configurada |
| GET | `/admin/models/{provider}` | Modelos disponíveis no provedor (`google` ou `openai`) |
| POST | `/admin/models/test` | Testa um modelo (`{provider, model}`) |

## Avaliação (**admin**)

| Método | Rota | Descrição |
|---|---|---|
| GET / POST | `/evals/cases` | Lista / cria casos de teste |
| PUT / DELETE | `/evals/cases/{id}` | Edita / exclui caso |
| POST | `/evals/cases/import` | Importa casos em lote |
| POST | `/evals/cases/generate` | Agenda geração de casos sintéticos (`{count}`) |
| GET / POST | `/evals/runs` | Lista / inicia execuções (`{name, case_ids}`) |
| GET / DELETE | `/evals/runs/{id}` | Detalhes com resultados / exclui |

## Saúde

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Estado do banco, do Qdrant e das chaves de API |
