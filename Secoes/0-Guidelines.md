# Guidelines de redação — TCC USP/Esalq

> Arquivo de referência obrigatória antes de redigir ou revisar qualquer seção.

---

## 1. Parágrafos

- Máximo **5 a 7 linhas** por parágrafo (≈ 60–85 palavras).
- Cada parágrafo deve ter **uma ideia central**; não acumule argumentos distintos.
- Nenhum parágrafo deve terminar sem indicar a ponte para o próximo.

---

## 2. Referências e citações

### Formato das entradas bibliográficas
- Sobrenome do autor com **apenas a primeira letra maiúscula** (não em caixa alta).
- Ano logo após o nome do autor: `Wiegers, K.; Beatty, J. 2013.`
- Títulos em **sentence case**: somente a primeira palavra e nomes próprios em maiúscula.
- Siglas/acrônimos permanecem em maiúscula: LLMs, PLN, ER, AI.

### Citações no texto (norma USP/Esalq — não seguir ABNT puro)
- **Citação parentética**: sobrenome com primeira letra maiúscula apenas — `(Pohl, 2025)`, não `(POHL, 2025)`.
- **Citação narrativa**: mesmo formato — `Pohl (2025) classifica...`
- **Sem localizador de seção**: ❌ `(Pohl, 2025, §25.2)` — o símbolo § é reservado a referências jurídicas; ABNT usa página `(Pohl, 2025, p. X)`. Preferir `(Pohl, 2025)` sem localizador.
- Múltiplos autores separados por ponto e vírgula: `(Wiegers; Beatty, 2013)`.
- Múltiplas obras separadas por ponto e vírgula: `(Pohl, 2025; Sommerville, 2016)`.
- ❌ **Nunca usar caixa alta** nas citações no texto — esse é o padrão ABNT, não o da USP.

### Integridade dos dados citados
- **Nunca inventar estatísticas.** Verificar o dado diretamente na fonte antes de citar.
- Se o dado vem de uma fonte secundária (apud), indicar explicitamente ou usar a fonte primária.
- Estatísticas corretas confirmadas até o momento:
  - "40% a 50% dos defeitos em requisitos" → fonte: Davis (2005) via Wiegers; Beatty (2013), p. 4.
  - "cem vezes mais" (custo de correção tardia) → fonte: Boehm (1981) — **não está na lista de referências atual; não usar sem adicionar a referência.**

### Referências permitidas no texto atual
As únicas referências válidas para uso no texto são as listadas em `4-Referencias.md`:
- Almeida et al. (2025)
- Bashir et al. (2025)
- Cheng et al. (2025)
- Gulli (2025)
- Guo et al. (2025)
- Kamsties et al. (2001)
- Pohl (2025)
- Schut; Gal; Farquhar (2025)
- Sommerville (2016)
- Wiegers; Beatty (2013)
- Virissimo (2014)
- Zadenoori et al. (2025)
- Andrade (2026) — repositório do pipeline *(a ser adicionado)*

**Qualquer outra referência deve ser adicionada em `4-Referencias.md` antes de ser citada no texto.**

---

## 3. Template USP/Esalq — regras por seção

| Seção | Regras |
|---|---|
| **Introdução** | Máx. 2 páginas · sem subtópicos · objetivo no último parágrafo |
| **Metodologia** | Descrição detalhada de materiais e métodos · subtópicos permitidos |
| **Resultados Preliminares** | Apresentar dados obtidos · subtópicos permitidos |
| **Referências** | Somente obras citadas no texto · formato ABNT |

---

## 4. Consistência técnica do pipeline

As descrições técnicas abaixo são definitivas. **Não alterar sem revisar o código em `Orchestrator/`.**

### Taxonomia de ambiguidades (Pohl, 2025, §25.3)
Apenas cinco tipos válidos — usar exatamente esses termos:
- `lexical` · `sintática` · `semântica` · `referencial` · `vaguidade`

❌ Não usar: "lógica", "pragmático-contextual", "domínio", ou qualquer outro rótulo.

### Agente 1 — Detector de Ambiguidades e Concern Mixing
- **Context-blind**: recebe **apenas** `base_requirement_text`.
- Não recebe contexto, glossário, domínio ou metadados do corpus.
- Output contém dois flags booleanos **independentes**: `has_ambiguity` e `has_concern_mixing`.
- `has_concern_mixing: true` quando a sentença contém simultaneamente uma ação funcional e um critério de qualidade (Pohl §25.2) — ortogonal a `has_ambiguity`; os dois podem ser `true` ao mesmo tempo.

### Agente 2 — Verificação de Resolubilidade
- Context-aware: recebe requisito + `controlled_context` + output do Agente 1.
- Status por ambiguidade: `resolvable | unresolved | not_applicable`.
- Status global: `fully_resolvable | unresolved | no_ambiguity`.
- Define `structural_issue: concern_mixing` quando `has_concern_mixing: true` no output do Agente 1 — independente de `has_ambiguity`.

### Agente 3 — Estruturador
- Invocado **apenas** quando status global é `fully_resolvable` ou `no_ambiguity`.
- Tipos de saída: `functional_requirement | quality_requirement | constraint`.
- Quando `concern_mixing`: decompõe obrigatoriamente em FR + QR (Pohl §25.2).

### Consolidador
- **Não é um agente LLM** — é um script Python determinístico.
- Monta o `05_final_output.json` a partir dos outputs dos três agentes.

### Formato de comunicação entre agentes
- **YAML** — não XML, não Markdown, não JSON.

### Condições de contexto
| Código | Descrição |
|---|---|
| C0 | Sem contexto (`controlled_context` vazio) |
| C1 | Contexto geral (domínio e glossário) |
| C2 | Contexto resolutivo (+ regras de negócio e restrições) |

### Corpus e execuções
- 14 requisitos × 3 condições = **42 execuções**.
- Quatro categorias: Cat-01 Estrutural · Cat-02 Linguística · Cat-03 Domínio · Cat-04 Controle.

### Modelos LLM utilizados
- `qwen3.5:4b`, `qwen3.5:9b`, `gemma4-e4b` e `mistral:7b` via Ollama
- OpenAI (opcional)
- Parâmetros de determinismo: `temperature=0.0`, `think=false`

---

## 5. Terminologia padronizada

| Usar | Não usar |
|---|---|
| resolubilidade | resolvabilidade |
| `fully_resolvable` / `unresolved` / `no_ambiguity` | "parcialmente resolúveis", "bloqueantes" |
| concern mixing | mistura de preocupações (pode aparecer como tradução, mas usar o termo em inglês em itálico) |
| pipeline multi-agente | sistema multi-agente (preferir "pipeline" para precisão) |
| corpus controlado | conjunto de dados, dataset |
| avaliação quantitativa (D1–D4) | métricas automáticas (muito genérico) |

---

## 6. Avaliação do pipeline (evaluate.py)

Quatro dimensões binárias, score = D_corretas / D_aplicáveis:

| Dimensão | O que mede |
|---|---|
| **D1** `D1_has_ambiguity` | Detecção de ambiguidade pelo Agente 1a vs `expected_resolubility` |
| **D2** `D4_concern_mixing` | Detecção de concern mixing pelo Agente 1b vs `detect_concern_mixing` esperado — sem FP nem FN |
| **D3** `D2_route` | Rota tomada (`structured` / `signaling`) vs esperada dado o contexto da condição |
| **D4** `D3_output_complete` | Output substantivamente completo dado a rota tomada |

---

## 7. Formatação Word (template USP/Esalq confirmado)

Especificações extraídas diretamente do arquivo `Template TCC_PT (251, 252).docx`:

| Parâmetro | Valor |
|---|---|
| Fonte (corpo do texto) | Times New Roman ou Arial **11pt** |
| Espaçamento entre linhas | **1.5x** (`line=360`, `lineRule=auto`) |
| Margens (todos os lados) | **2.5 cm** (1418 twips) |
| Tamanho da página | A4 — área de texto: 16,0 cm × 23,44 cm |
| Espaço antes do parágrafo | **0 pt** |
| Espaço depois do parágrafo | **0 pt** |

**Sem espaço entre parágrafos** — o template já define `before=None / after=None` no estilo Normal. Se o Word adicionar espaço, corrigir via: selecionar todo o texto → Parágrafo → Espaçamento antes: 0 pt / depois: 0 pt.

**Estimativa de palavras por página:** ~400 palavras de prosa (calibrada contra o limite de 2 páginas da Introdução).

---

## 8. Itálico e formatação inline

- Termos em inglês: usar **aspas duplas**, não itálico — `"concern mixing"`, `"in-context learning"`, `"single responsibility"`. (Prof. Denis, comentário #6)
- Siglas: definir na primeira ocorrência — `"Large Language Models" (LLMs)`; usar apenas a sigla nas ocorrências seguintes.
- Termos portugueses com ênfase tipográfica: *verificável*, *completo* — itálico permitido.
- Nomes de campos do pipeline em `code`: `has_ambiguity`, `controlled_context`, `structural_issue`.
