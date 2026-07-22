# Plano de Análise dos Resultados

Este documento registra como os resultados das execuções do corpus serão analisados na seção **3. Resultados Preliminares**, articulando as quatro dimensões quantitativas (D1–D4) com os quatro tipos de gráficos produzidos pelo pipeline de avaliação.

---

## Estrutura geral da análise

A análise segue três camadas sucessivas, da visão consolidada à evidência granular:

1. **Perfil geral do pipeline** — consolidated bar (D1–D4 agregados)
2. **Impacto do contexto** — context line (D3/D4 por C0/C1/C2)
3. **Capacidade por tipo de defeito** — category bar (D1–D4 por categoria)
4. **Localização dos erros** — heatmaps por modelo (diagnóstico)

O conjunto foi desenhado com o pipeline como unidade de análise principal; os modelos funcionam como variável de controle para validar robustez dos achados, não como objeto de comparação.

---

## Gráfico 1 — Consolidated bar (perfil geral do pipeline)

**Arquivo:** `pipeline_consolidated.png`

**O que mostra:** acurácia média de D1–D4 sobre todas as execuções (todos os modelos e condições). Uma barra por dimensão, modelos e condições agregados.

**Como analisar:**

- **Perfil de acerto do pipeline como sistema:** quais dimensões o pipeline domina e quais são seus pontos fracos estruturais, independentemente do modelo ou condição.
- **D1 e D2 como linha de base de detecção:** valores altos confirmam que os agentes de detecção funcionam consistentemente. Valores baixos indicam problema conceitual nos prompts, não sensibilidade ao contexto.
- **D3 (Rota) como dimensão mais variável:** por depender do contexto, espera-se que D3 tenha acurácia inferior à média de D1/D2/D4 quando consolidado sobre C0/C1/C2 — o dado de C0 "puxa" a média para baixo.
- **D4 (Output) próximo de 100%:** quando o Agente 3 é acionado, o output tende a ser completo. Valor baixo aqui indicaria falha no próprio agente, não no roteamento.

**Leitura esperada na seção 3:** apresentar primeiro o perfil consolidado para estabelecer o baseline do pipeline; depois detalhar D3 pelo gráfico de linha contextual.

---

## Gráfico 2 — Context line (impacto do contexto)

**Arquivo:** `context_line__D3_D4.png`

**O que mostra:** acurácia de D3 (Rota) e D4 (Output) pelas três condições de contexto (C0, C1, C2), com uma linha por modelo. Eixo X ordinal e progressivo (C0 < C1 < C2).

**Como analisar:**

- **Inclinação das linhas:** linhas com inclinação positiva confirmam que o contexto melhora o desempenho — resultado esperado para D3 (Rota), que depende do Agente 2. Linhas planas indicam insensibilidade ao contexto.
- **Onde ocorre o maior ganho — C0→C1 ou C1→C2:** se o salto está em C0→C1, o glossário e a descrição de domínio já são suficientes; se o salto está em C1→C2, a melhoria depende especificamente de regras de negócio e restrições operacionais — o que tem implicação prática direta para como o contexto deve ser fornecido em uso real.
- **Convergência entre modelos:** quando todas as linhas sobem juntas, o efeito do contexto é consistente e não é artefato de um modelo específico. Isso fortalece a evidência metodológica.
- **D4 próximo de 100% em todas as condições:** confirma que o Agente 3 é robusto quando acionado; a variabilidade está no acionamento (D3), não na qualidade do output.

**Leitura esperada na seção 3:** este é o gráfico central para a pergunta de pesquisa. Identificar a magnitude do ganho de C0 para C2 em D3 e verificar se o padrão é consistente entre modelos.

---

## Gráfico 3 — Category bar (capacidade por tipo de defeito)

**Arquivo:** `category_bar__D1_D4.png`

**O que mostra:** acurácia de D1–D4 por categoria do corpus (Cat-01 a Cat-04), grade 2×2 com um painel por modelo. Barras agrupadas por categoria; cores por dimensão.

**Como analisar:**

- **Cat-01 (Estrutural) — foco em D2 (ConcernMix):** esta categoria testa especificamente a detecção de concern mixing. D2 baixo em Cat-01 indica que o Agente 1b falha justamente nos casos para os quais foi projetado.
- **Cat-02 (Linguística) — foco em D1 e D3:** requisitos com ambiguidades textuais variadas. D1 baixo indica falso negativo na detecção; D3 baixo indica que mesmo com detecção correta a rota falhou.
- **Cat-03 (Domínio) — foco em D3 por condição:** ambiguidades dependentes de conhecimento especializado são as que mais devem se beneficiar do contexto C2. D3 baixo em Cat-03 mesmo em C2 indica que o contexto fornecido foi insuficiente para as ambiguidades de domínio.
- **Cat-04 (Controle) — foco em D1 e D2 como falsos positivos:** requisitos intencionalmente sem ambiguidade ou concern mixing. D1 ou D2 incorretos em Cat-04 são falsos positivos — o pipeline sinalizou problema onde não havia. É a métrica de precisão do sistema.

**Consistência entre modelos:** quando o mesmo padrão se repete nos quatro painéis, o achado é atribuível ao pipeline; quando apenas um modelo se diferencia, a causa é capacidade do modelo específico.

**Leitura esperada na seção 3:** identificar se há categorias onde o pipeline sistematicamente falha (problema de design do agente) vs. categorias onde apenas alguns modelos falham (problema de capacidade do modelo).

---

## Gráfico 4 — D1 Erro por categoria (Ambiguidade — FP/FN)

**Arquivo:** `error_type__D1_ambiguidade.png`

**O que mostra:** contagem de falsos positivos (FP) e falsos negativos (FN) de D1 (Ambiguidade) por categoria do corpus, grade 2×2 por modelo. Um FP ocorre quando o Agente 1a sinaliza ambiguidade em requisito que a referência manual classifica como sem ambiguidade; um FN ocorre quando o agente não detecta ambiguidade onde ela existe.

**Como analisar:**

- **Cat-04 concentra os FP de D1:** requisitos de controle são intencionalmente sem ambiguidade; erros nessa categoria são exclusivamente FP — indicador direto de precisão do agente.
- **FN em Cat-02/03:** falsos negativos nas categorias de ambiguidade linguística e de domínio indicam limitação de cobertura do Agente 1a — o agente sub-detecta nesses tipos de defeito.
- **Consistência de padrão entre modelos:** FP e FN concentrados nos mesmos requisitos em todos os modelos sugerem limitação do prompt do agente, não do modelo; variação entre modelos aponta diferença de capacidade.

**Leitura esperada na seção 3:** mapear onde o Agente 1a erra por excesso (FP) vs. por omissão (FN), e se o padrão é consistente entre modelos.

---

## Gráfico 5 — D2 Erro por categoria (ConcernMix — FP/FN)

**Arquivo:** `error_type__D2_concernmix.png`

**O que mostra:** contagem de falsos positivos (FP) e falsos negativos (FN) de D2 (ConcernMix) por categoria, grade 2×2 por modelo. Apenas REQ-01 (dentro de Cat-01) tem `detect_concern_mixing` esperado; os demais requisitos de Cat-01 (REQ-02, REQ-03) e todas as outras categorias não têm concern mixing esperado, portanto erros nessas instâncias são necessariamente FP.

**Como analisar:**

- **FP em Cat-02/03/04:** o Agente 1b sinalizou concern mixing onde não há — indica sensibilidade excessiva ou problema de prompt para determinados padrões linguísticos.
- **FN em Cat-01:** se o agente não detectar concern mixing nos requisitos estruturais, a rota de decomposição não será acionada — erro com impacto direto no output final.
- **Ausência de FN nos resultados observados:** todos os modelos testados produziram apenas FP, sem FN — indicando que o Agente 1b tende à super-detecção para os requisitos deste corpus.

**Leitura esperada na seção 3:** caracterizar o perfil de erro do Agente 1b como orientado a FP (alta sensibilidade, baixa precisão) ou a FN (baixa sensibilidade), e identificar se alguma categoria concentra FP de forma sistemática.

---

## Gráfico 5b — D3 Rota: erros por contexto (FP/FN × C0/C1/C2)

**Arquivo:** `error_type__D3_rota_por_contexto.png`

**O que mostra:** contagem de erros de rota (D3) por condição de contexto (C0, C1, C2), separados em FP e FN, grade 2×2 por modelo.

- **FP (structured indevido):** o pipeline escolheu a rota de estruturação quando deveria ter sinalizado ambiguidade não resolúvel — sobre-confiança, resultado de contexto insuficiente ou ambiguidade de domínio que o agente 2 não conseguiu resolver.
- **FN (signaling indevido):** o pipeline enviou para sinalização quando o contexto fornecido era suficiente para resolver — sub-detecção, possivelmente por conservadorismo do Agente 2.

**Por que este gráfico é complementar ao context_line:** o context_line mostra acurácia subindo de C0 para C2; este mostra explicitamente quantos erros são eliminados e de que tipo. Permite distinguir se o contexto reduz mais os FP (a maioria do pipeline sobre-confia em C0) ou os FN (o pipeline é sub-confiante em C0).

**D1 e D2 não aparecem aqui por design:** são context-free — o mesmo resultado é reutilizado em C0/C1/C2, portanto a contagem de erros seria idêntica nas três condições e não carrega informação nova.

**Leitura esperada na seção 3:** verificar se a redução de erros de C0 para C2 é predominantemente de FP ou FN, e se o padrão é consistente entre modelos. Redução assimétrica (só FP ou só FN) revela o perfil de conservadorismo do Agente 2.

---

## Gráfico 6 — Heatmaps (diagnóstico por modelo)

**Arquivos:** `heatmap__run_00X__<modelo>.png` (um por modelo)

**O que mostra:** grade de 42 linhas (14 requisitos × 3 condições) × 4 colunas (D1–D4), com células verdes (correto), vermelhas (incorreto) ou cinzas (N/A). Mapa de erros granular por modelo.

**Como analisar:**

- **Padrão de linha horizontal vermelha em D1 (C0/C1/C2 idênticos):** confirma falso negativo estrutural do modelo em um requisito específico — independente de contexto, como esperado para D1.
- **D3 mudando de vermelho para verde entre condições:** evidência visual direta de que o contexto resolutivo (C2) corrigiu a decisão de rota em um requisito específico.
- **Cat-04 (REQ-12/13/14) em D1 e D2:** células vermelhas nesses requisitos são falsos positivos — o modelo sinalizou problema onde o corpus garante que não há.
- **Correlação D1+D3 vermelhos na mesma linha:** erro propagado entre agentes (detecção errada contaminou a rota). Quando apenas D3 é vermelho com D1 verde: erro de roteamento isolado no Agente 2.

**Leitura esperada na seção 3:** usar o heatmap para apontar requisitos âncora — aqueles com erros transversais a múltiplos modelos (limitação do corpus ou da tarefa) vs. erros exclusivos de um modelo (limitação do modelo).

---

## Sequência de análise para a seção 3

```
1. Context line              → impacto do contexto em D3/D4 (a pergunta central — RQ1)
2. Category bar              → capacidade por tipo de defeito (RQ3)
3. D1 Erro por categoria     → FP/FN do Agente 1a — onde e como erra (RQ4)
4. D2 Erro por categoria     → FP/FN do Agente 1b — onde e como erra (RQ4)
5. D3 Erro por contexto      → redução de erros de rota de C0 a C2 (RQ1 + RQ4)
6. Heatmaps                  → diagnóstico granular por requisito e modelo
```

---

## Perguntas de pesquisa e gráficos correspondentes

| Pergunta | Gráfico principal |
|---|---|
| O contexto melhorou o desempenho em D3/D4? | Context line |
| O ganho veio em C0→C1 ou em C1→C2? | Context line (inclinação) |
| O pipeline funciona para cada tipo de defeito? | Category bar |
| O Agente 1a gera mais FP ou FN, e em quais categorias? | D1 Erro por categoria |
| O Agente 1b gera mais FP ou FN, e em quais categorias? | D2 Erro por categoria |
| Quantos erros de rota são eliminados de C0 para C2? | D3 Erro por contexto |
| O contexto reduz FP ou FN de rota — ou ambos? | D3 Erro por contexto (tipo de barra) |
| Onde especificamente ocorreram os erros? | Heatmap |
| Os erros propagaram entre agentes (D1+D3 correlacionados)? | Heatmap |
| Os achados são consistentes entre modelos? | Todos os gráficos (padrão nos 4 painéis) |

---

## Notas metodológicas para redigir a seção 3

- D1 e D2 são **invariantes por design** ao contexto: não interpretar variação residual entre condições como efeito de contexto — atribuir a possível instabilidade de execução ou ao número pequeno de casos por célula.
- O score é a razão `correct/applicable`, não `correct/4`: dimensões marcadas N/A não penalizam o modelo.
- A comparação entre modelos é **exploratória e serve à validação de robustez**: o corpus tem 14 requisitos e os modelos foram testados em uma única configuração de parâmetros. Os resultados caracterizam o comportamento do pipeline nessas condições, sem pretensão de generalização estatística ou de ranking entre modelos.
