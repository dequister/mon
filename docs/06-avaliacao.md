# 6. Avaliação do RAG

A tela **Avaliação do RAG** permite medir a qualidade do sistema de forma repetível e comparar configurações
(modelo, top-k, rerank, tamanho de chunk). Cada execução guarda um retrato da configuração usada.

## 6.1 Casos de teste

Um caso de teste contém:

- **pergunta**;
- **resposta de referência** (opcional) — usada na métrica de correção;
- **documentos esperados** (opcional) — nomes dos arquivos que deveriam ser recuperados;
- **tags** — para organizar (ex.: `matrícula`, `estágio`, `sintético`).

Os casos podem ser criados na interface, importados/exportados em JSON ou **gerados sinteticamente**: o LLM recebe
trechos aleatórios da base (amostragem aleatória do Qdrant) e cria uma pergunta, a resposta e o documento de
origem. Casos sintéticos devem ser revisados antes de entrar nos resultados do trabalho.

Formato de importação:

```json
[
  {
    "question": "Qual a carga horária mínima do estágio supervisionado?",
    "expected_answer": "160 horas.",
    "expected_documents": ["regulamento-estagio.pdf"],
    "tags": ["estágio"]
  }
]
```

## 6.2 Métricas de recuperação

Calculadas sobre a lista final de trechos enviados ao LLM (após o rerank), comparando nomes de arquivo com os
documentos esperados. Só são calculadas quando o caso tem documentos esperados.

Seja *R* = (r₁, ..., rₙ) a lista ordenada de arquivos dos trechos recuperados e *E* o conjunto de documentos
esperados:

| Métrica | Definição | Interpretação |
|---|---|---|
| **Hit rate** | 1 se algum rᵢ ∈ E; senão 0 | Pelo menos um documento correto chegou ao contexto? |
| **MRR** (*Mean Reciprocal Rank*) | 1 / posição do primeiro rᵢ ∈ E (0 se nenhum) | Quão no topo está o primeiro documento correto (Voorhees, 1999) |
| **Recall** | \|{rᵢ} ∩ E\| / \|E\| | Fração dos documentos esperados recuperados |
| **Precisão de contexto** | \|{i : rᵢ ∈ E}\| / n | Fração do contexto que vem de documentos esperados |

Os valores da execução são as médias sobre os casos (Manning, Raghavan e Schütze, 2008).

## 6.3 Métricas de geração (LLM como juiz)

Inspiradas no RAGAS (Es *et al.*, 2023) e na abordagem *LLM-as-a-judge* (Zheng *et al.*, 2023). O mesmo modelo
configurado no sistema recebe a pergunta, o contexto, a resposta de referência e a resposta do Mon, e devolve em
JSON notas de 0 a 1 e uma justificativa:

| Métrica | Pergunta ao juiz |
|---|---|
| **Fidelidade** (*faithfulness*) | A resposta está sustentada pelos trechos do contexto? (detecta alucinação) |
| **Relevância** (*answer relevance*) | A resposta atende diretamente à pergunta? |
| **Correção** (*correctness*) | A resposta concorda com a resposta de referência? (só com referência) |

Também são registradas a **latência média** e o **percentil 95** da latência por pergunta.

## 6.4 Execução

1. O administrador clica em **Executar avaliação** (todos os casos ou os selecionados).
2. É criado um registro `eval_runs` com a configuração atual e um job `eval_run`.
3. O worker responde cada pergunta com o pipeline real do Mon (sem histórico), calcula as métricas e grava um
   `eval_results` por caso, permitindo acompanhar o progresso em tempo real.
4. Ao final, as médias ficam em `eval_runs.metrics`.

## 6.5 Limitações

- O juiz é o próprio LLM configurado; trocar o modelo pode alterar as notas. Para comparar configurações, use o
  mesmo juiz.
- As métricas de recuperação dependem da qualidade dos documentos esperados cadastrados.
- Casos sintéticos tendem a favorecer a recuperação, pois a pergunta nasce do próprio trecho.

## 6.6 Sugestão de protocolo experimental para o TCC

1. Montar um conjunto de 30 a 50 perguntas reais (ex.: dúvidas frequentes da secretaria), com documentos esperados
   e respostas de referência validadas.
2. Executar a avaliação com a configuração padrão (linha de base).
3. Variar um fator por vez — rerank ligado/desligado, top-n, tamanho de chunk (reindexando), modelo — e comparar.
4. Reportar as métricas médias, a latência e exemplos qualitativos (acertos e falhas).
