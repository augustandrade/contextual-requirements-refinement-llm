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
- **Sem localizador de seção**: ❌ `(Pohl, 2025, §25.2)` — usar `(Pohl, 2025)` sem localizador.
- Múltiplos autores separados por ponto e vírgula: `(Wiegers; Beatty, 2013)`.
- Múltiplas obras separadas por ponto e vírgula: `(Pohl, 2025; Sommerville, 2016)`.
- ❌ **Nunca usar caixa alta** nas citações no texto.

### Integridade dos dados citados
- **Nunca inventar estatísticas.** Verificar o dado diretamente na fonte antes de citar.
- Estatísticas confirmadas:
  - "40% a 50% dos defeitos em requisitos" → fonte: Davis (2005) via Wiegers; Beatty (2013), p. 4.

### Referências válidas para uso no texto
- Almeida et al. (2025)
- Andrade (2026) — repositório do pipeline *(a ser adicionado)*
- Bashir et al. (2025)
- Cheng et al. (2025)
- Gulli (2025)
- Guo et al. (2025)
- Kamsties et al. (2001)
- Pohl (2025)
- Schut; Gal; Farquhar (2025)
- Sommerville (2016)
- Veizaga et al. (2024)
- Wiegers; Beatty (2013)
- Zadenoori et al. (2025)

**Qualquer outra referência deve ser adicionada antes de ser citada no texto.**

---

## 3. Template USP/Esalq — regras por seção

| Seção | Regras |
|---|---|
| **Introdução** | Máx. 2 páginas · sem subtópicos · objetivo no último parágrafo |
| **Metodologia** | Descrição detalhada de materiais e métodos · subtópicos permitidos |
| **Resultados e Discussão** | Apresentar e discutir dados · subtópicos por bloco de análise |
| **Referências** | Somente obras citadas no texto · formato ABNT |

---

## 4. Consistência técnica do pipeline

As descrições abaixo refletem o estado atual do código em `Orchestrator/`. **Não alterar sem revisar o código.**

### Corpus e execuções

| Item | Valor |
|---|---|
| Requisitos | **15** textos-base |
| Condições de contexto | **4** (C0, C1, C2, C3) |
| Instâncias experimentais | **60** (15 × 4) |
| Modelos avaliados | **7** |
| Total de execuções | **420** (60 × 7) |

### Categorias do corpus

| Código | Nome | Gabarito D1 |
|---|---|---|
| Cat-01 | Estrutural | Positivo (ambiguidade esperada) |
| Cat-02 | Linguística | Positivo |
| Cat-03 | Domínio | Positivo |
| Cat-04 | Vaguidade | Positivo |
| Cat-05 | Controle | **Negativo** (sem ambiguidade esperada) |

### Condições de contexto

| Código | Descrição |
|---|---|
| C0 | Sem contexto (`controlled_context` ausente) |
| C1 | Contexto genérico: domínio do sistema e glossário periférico |
| C2 | Contexto resolutivo: acumula C1 + definição operacional, regra de negócio ou restrição que endereça diretamente o fragmento ambíguo |
| C3 | Contexto irrelevante: acumula C1 + conteúdo específico sobre aspecto diferente do requisito, nunca o fragmento ambíguo |

C0 é executado para todos os requisitos. C1, C2 e C3 apenas quando o Agente 1 detecta ambiguidade.

### Modelos LLM utilizados

`qwen3.5:4b` · `qwen3.5:9b` · `gemma3:4b` · `mistral:7b` · `llama3.1:8b` · `phi4-mini` · `deepseek-r1:7b`

Executados localmente via Ollama. Parâmetros: `temperature=0.0`, `think=false`.

### Taxonomia de ambiguidades (Pohl, 2025)

Cinco tipos válidos — usar exatamente esses termos:

`lexical` · `syntactic` · `semantic` · `referential` · `vagueness`

❌ Não usar: "lógica", "pragmático-contextual", "domínio", ou qualquer outro rótulo.

### Agente 1 — Detector de Ambiguidades

- **Context-blind**: recebe **apenas** `base_requirement_text`.
- Output principal: `has_ambiguity` (booleano).
- Classifica ambiguidades segundo a taxonomia de Pohl (2025) — campo `ambiguity_type`.
- Por ser independente do contexto, executa **uma única vez por requisito**; o output é reutilizado nas quatro condições (C0–C3).

### Agente 2 — Verificação de Resolubilidade

- Context-aware: recebe requisito + `controlled_context` + output do Agente 1.
- Status por ambiguidade (campo `resolubility_status`):
  - `resolvable` — evidência direta seleciona uma única interpretação.
  - `unresolved` — nenhuma evidência seleciona ou elimina qualquer interpretação.
  - `false_positive` — evidência mostra que interpretações reportadas não têm base no texto.
- Status global (`overall_resolubility.status`):
  - `fully_resolvable` — todas as ambiguidades são `resolvable` ou `false_positive`.
  - `unresolved` — ao menos uma ambiguidade permanece `unresolved`.
  - `no_ambiguity` — Agente 1 não detectou ambiguidade (bloco sintético determinístico).

### Agente 3 — Estruturador

- Invocado **apenas** quando status global é `fully_resolvable` ou `no_ambiguity`.
- Rota `signaling` encerra o pipeline sem invocar o Agente 3.
- Tipos de saída (`requirement_type`): `functional_requirement` · `quality_requirement` · `constraint`.
- Fragmentos `resolvable` têm o texto substituído pelo `supported_interpretation`; fragmentos `false_positive` preservam o texto original.

### Consolidador

- **Não é um agente LLM** — script Python determinístico.
- Monta o `final_output.json` integrando outputs dos três agentes e a decisão de roteamento.
- Executado em todas as condições, inclusive `signaling`.

### Roteamento

| Status global | Rota | Agente 3 invocado? |
|---|---|---|
| `fully_resolvable` | `structured` | Sim |
| `no_ambiguity` | `structured` | Sim |
| `unresolved` | `signaling` | Não |

### Formato de comunicação entre agentes

**YAML** — não XML, não Markdown, não JSON.

---

## 5. Protocolo de avaliação (evaluate.py)

Quatro blocos de análise — sem gabarito de rota esperada no Bloco 2 (descritivo).

| Bloco | Métrica principal | Dimensão | RQ |
|---|---|---|---|
| **Bloco 1** | D1 — detecção de ambiguidade pelo Agente 1 vs. `category_id` | `D1_has_ambiguity` | RQ2 |
| **Bloco 2** | Sensibilidade ao contexto — ΔRoute(C2−C0), ΔRoute(C3−C0), Δ(C2−C3), ganhos C0→C1 e C1→C2 | `act_route` | RQ1 |
| **Bloco 3** | Classificação taxonômica — tipo detectado vs. `taxonomy_accepted_types` | `match` | RQ3 |
| **Bloco 4** | Integridade estrutural do output dado a rota tomada | `D_output_integrity` | complementar |

**Gabarito D1**: derivado de `category_id` — Cat-01 a Cat-04 são positivos; Cat-05 é o único negativo. Não usa `taxonomy_accepted_types` como proxy (campo ausente em Cat-01).

**Gabarito Bloco 3**: `taxonomy_accepted_types` preenchido apenas em Cat-02, Cat-03 e Cat-04. Critério de acerto: ao menos um tipo detectado presente no conjunto aceito.

**Bloco 2 é descritivo** — não existe gabarito de rota esperada por condição. A análise compara rotas observadas entre condições.

---

## 6. Terminologia padronizada

| Usar | Não usar |
|---|---|
| resolubilidade | resolvabilidade |
| `fully_resolvable` / `unresolved` / `no_ambiguity` | "parcialmente resolúveis", "bloqueantes" |
| pipeline multi-agente | sistema multi-agente |
| corpus controlado | conjunto de dados, dataset |
| texto-base | requisito (quando a distinção com instância experimental importa) |
| instância experimental | execução, caso (quando referindo-se a requisito × condição) |
| rota `structured` / rota `signaling` | rota de estruturação / rota de sinalização |
| "concern mixing" (entre aspas, em inglês) | mistura de preocupações |

---

## 7. Formatação Word (template USP/Esalq)

| Parâmetro | Valor |
|---|---|
| Fonte (corpo do texto) | Times New Roman ou Arial **11pt** |
| Espaçamento entre linhas | **1.5x** |
| Margens (todos os lados) | **2.5 cm** |
| Tamanho da página | A4 — área de texto: 16,0 cm × 23,44 cm |
| Espaço antes/depois do parágrafo | **0 pt** |

**Estimativa de palavras por página:** ~400 palavras de prosa.

---

## 8. Itálico e formatação inline

- Termos em inglês: usar **aspas duplas**, não itálico — `"concern mixing"`, `"in-context learning"`.
- Siglas: definir na primeira ocorrência — `"Large Language Models" (LLMs)`; usar apenas a sigla depois.
- Nomes de campos do pipeline: usar `code` — `has_ambiguity`, `controlled_context`, `resolubility_status`.
- Termos portugueses com ênfase tipográfica: *verificável*, *completo* — itálico permitido.
