# 1. Visão geral

## 1.1 Problema

Instituições de ensino produzem grande volume de documentos (editais, regulamentos, resoluções, calendários,
planilhas de disciplinas, atas digitalizadas). A informação existe, mas está dispersa em formatos heterogêneos e
muitas vezes em PDFs escaneados, sem texto pesquisável. Encontrar uma regra específica exige tempo e conhecimento
prévio de onde procurar — um problema típico de **gestão do conhecimento** e de **eficiência de processos**,
temas centrais da Engenharia de Produção.

## 1.2 Objetivo

Desenvolver o **Mon**, um assistente virtual que responde perguntas em linguagem natural com base exclusivamente
nos documentos da instituição, indicando de forma transparente as fontes consultadas em cada resposta.

### Objetivos específicos

1. Ingerir documentos em múltiplos formatos, incluindo documentos digitalizados (OCR).
2. Indexar o conteúdo em um banco vetorial com metadados que permitam rastrear e reindexar cada documento.
3. Responder perguntas com a técnica RAG (*Retrieval-Augmented Generation*), citando as fontes.
4. Oferecer uma área administrativa para carga de documentos, acompanhamento de jobs e escolha de modelos.
5. Medir a qualidade do sistema com métricas objetivas de recuperação e de geração.

## 1.3 Escopo

**Incluído**

- Autenticação por usuário e senha (inicialmente apenas o administrador `admin`).
- Chat com histórico de conversas por usuário.
- Upload manual de arquivos (arrastar e soltar) e sincronização com uma pasta de arquivos.
- Seleção, pelo administrador, do modelo de linguagem entre os disponíveis na Google e na OpenAI.
- Avaliação do RAG com casos de teste manuais, importados ou sintéticos.

**Fora do escopo (trabalhos futuros)**

- Cadastro de usuários pela interface e perfis de acesso por documento.
- Integração direta com repositórios externos (SharePoint, Google Drive, SEI).
- Busca híbrida (vetorial + lexical) e extração estruturada de tabelas em PDFs.

## 1.4 Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | O sistema deve autenticar usuários por usuário e senha. |
| RF02 | O usuário deve conversar com o assistente e ver respostas em tempo real (streaming). |
| RF03 | Cada resposta deve listar as fontes consultadas (arquivo, página/aba, trecho, relevância). |
| RF04 | O usuário deve listar, renomear e excluir suas conversas. |
| RF05 | O administrador deve enviar arquivos por arrastar e soltar. |
| RF06 | O sistema deve aplicar OCR apenas em páginas escaneadas. |
| RF07 | Reenviar um documento alterado deve substituir seus vetores, sem deixar resíduos. |
| RF08 | O administrador deve acompanhar jobs de indexação e sincronização. |
| RF09 | O administrador deve escolher o modelo de linguagem entre os disponíveis nos provedores. |
| RF10 | O administrador deve executar avaliações do RAG e consultar métricas. |

## 1.5 Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF01 | Execução conteinerizada (Docker Compose) e reproduzível. |
| RNF02 | Senhas armazenadas com hash bcrypt; API protegida por JWT. |
| RNF03 | Processamento pesado (OCR, embeddings) fora do ciclo da requisição, em worker assíncrono. |
| RNF04 | Arquitetura em camadas com padrões de projeto que permitam trocar provedores de IA. |
| RNF05 | Interface responsiva em português do Brasil. |
