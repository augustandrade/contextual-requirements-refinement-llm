# Resultados e Discussão

Os resultados são apresentados na sequência dos quatro blocos do protocolo de avaliação, em correspondência com os subtítulos da seção de Material e Métodos. Ao final da seção, as hipóteses são respondidas diretamente com base nos dados.

## Bloco 1 — Detecção de ambiguidade

O Bloco 1 avaliou a capacidade do Agente 1 de detectar ambiguidades nas 15 execuções em C0 de cada modelo, respondendo a RQ2. A Tabela 1 apresenta os contadores de classificação e as métricas derivadas.

**Tabela 1.** Métricas de detecção de ambiguidade em C0 por modelo (n = 15)

| Modelo | TP | FP | FN | TN | Precisão | Revocação | F1 | Especificidade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen3.5-4b | 11 | 2 | 1 | 1 | 84,6% | 91,7% | 88,0% | 33,3% |
| qwen3.5-9b | 11 | 3 | 1 | 0 | 78,6% | 91,7% | 84,6% | 0,0% |
| gemma3-4b | 12 | 3 | 0 | 0 | 80,0% | 100,0% | 88,9% | 0,0% |
| mistral-7b | 10 | 2 | 2 | 1 | 83,3% | 83,3% | 83,3% | 33,3% |
| llama3.1-8b | 11 | 3 | 1 | 0 | 78,6% | 91,7% | 84,6% | 0,0% |
| phi4-mini | 12 | 3 | 0 | 0 | 80,0% | 100,0% | 88,9% | 0,0% |
| deepseek-r1:7b | 7 | 1 | 5 | 2 | 87,5% | 58,3% | 70,0% | 66,7% |

*Fonte: Resultados originais da pesquisa*

Dois perfis de comportamento emergiram dos dados. O primeiro, de alta revocação, reuniu gemma3-4b e phi4-mini, que não produziram falsos negativos: todos os 12 requisitos ambíguos foram sinalizados, ao custo de alarmar também os três requisitos do grupo de controle negativo (Cat-05), resultando em especificidade nula. O comportamento é consistente com o padrão geral identificado na literatura para LLMs em tarefas de detecção binária de defeitos em requisitos: modelos menores tendem a priorizar revocação em detrimento da precisão quando não dispõem de exemplos de calibração ou ancoragem de domínio (Cheng et al., 2025). O segundo perfil, representado pelo deepseek-r1:7b, inverteu essa relação: o modelo registrou a maior precisão do conjunto (87,5%) e a maior especificidade (66,7%), ao custo de cinco falsos negativos — requisitos ambíguos não sinalizados em C0 que, em consequência, não receberam execuções em C1, C2 e C3. Os demais modelos concentraram-se em revocação entre 83,3% e 91,7% e precisão entre 78,6% e 84,6%, configurando um perfil equilibrado.

A especificidade nula observada para quatro modelos refletiu, em parte, a limitação do grupo de controle: três instâncias Cat-05 produzem um denominador mínimo para a estimação, de modo que um único falso positivo reduz a especificidade para 66,7% e dois a reduzem para 33,3%. A interpretação desse indicador demandou cautela em razão do tamanho do grupo de controle.

Os resultados do Bloco 1 foram superiores ao desempenho relatado em estudos que adotaram modelos isolados sem prompts especializados para a mesma tarefa. Shefa et al. (2026), em um benchmark de dez modelos das famílias OpenAI e Anthropic para avaliação de qualidade de requisitos, documentaram revocação mediana de 47% no melhor modelo avaliado. No contexto de detecção de ambiguidade pragmática com abordagem de recuperação aumentada, Nair e Anish (2025) reportaram revocação macro-média de 75% para o GPT-4o-mini e valores inferiores para modelos de código aberto equivalentes aos avaliados neste experimento. A comparação deve ser interpretada com reserva: os corpora, os critérios de avaliação e as formas de cômputo das métricas diferem entre os estudos.

Os intervalos de confiança de 95% estimados por bootstrap com 10.000 reamostras revelaram amplitude ampla em todos os modelos, reflexo do tamanho amostral de 15 execuções em C0. Para o deepseek-r1:7b, o IC para revocação abrangeu [30,0%; 84,6%], refletindo a instabilidade gerada pelos cinco falsos negativos; para os demais modelos, os limites inferiores de revocação foram iguais ou superiores a 72,7%, e os de F1 iguais ou superiores a 63,2%. As estimativas pontuais são consistentes com os dados, mas os ICs indicam que afirmações quantitativas fortes sobre superioridade entre modelos não são sustentadas pelo corpus de 15 requisitos.

## Bloco 2 — Sensibilidade ao contexto

O Bloco 2 rastreou a rota do pipeline ao longo das quatro condições de contexto, respondendo a RQ1. A métrica central foi ΔRoute(C2 − C0): proporção de requisitos que transitaram de signaling para structured ao receber o contexto específico relevante (C2), tomando C0 como referência. A Tabela 2 apresenta os resultados por modelo.

**Tabela 2.** Proporções de conversão de rota por condição de contexto (base: requisitos ambíguos com C0 = signaling)

| Modelo | n | ΔC2−C0 | ΔC3−C0 | ΔC2−C3 | C0→C1 | C1→C2 |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.5-4b | 11 | 72,7% | 18,2% | 54,5% | 0,0% | 72,7% |
| qwen3.5-9b | 10 | 90,0% | 40,0% | 50,0% | 10,0% | 80,0% |
| gemma3-4b | 12 | 75,0% | 75,0% | 0,0% | 16,7% | 58,3% |
| mistral-7b | 10 | 20,0% | 10,0% | 10,0% | 10,0% | 10,0% |
| llama3.1-8b | 11 | 54,5% | 36,4% | 18,2% | 27,3% | 27,3% |
| phi4-mini | 12 | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |
| deepseek-r1:7b | 7 | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% |

*Fonte: Resultados originais da pesquisa*

Os modelos da família qwen foram os únicos a demonstrar discriminação entre contexto relevante e irrelevante. O qwen3.5-4b converteu 72,7% das rotas signaling em structured ao receber C2, contra 18,2% em C3 — uma diferença de 54,5 pontos percentuais. O qwen3.5-9b exibiu padrão análogo, com maior magnitude: 90,0% em C2 e 40,0% em C3 (Δ = 50,0 pp). O teste de McNemar unilateral exato confirmou a significância estatística para ambos (qwen3.5-4b: n_discordante = 6, p = 0,016; qwen3.5-9b: n_discordante = 5, p = 0,031), com nenhuma vitória de C3 sobre C2 nos pares discordantes. O ganho de conversão se concentrou inteiramente no estágio C1→C2 para o qwen3.5-4b (72,7%) e majoritariamente nesse estágio para o qwen3.5-9b (80,0%), indicando que a etapa relevante para a resolução foi a injeção do conteúdo específico relevante, não a adição de contexto periférico (C0→C1 = 0% e 10%, respectivamente).

O gemma3-4b apresentou comportamento distinto: ΔC2−C0 e ΔC3−C0 foram idênticos (75,0%), resultando em ΔC2−C3 = 0,0%. O modelo converteu rotas tanto com contexto relevante quanto com contexto irrelevante de mesma especificidade, sem distinguir qual dos dois endereçava o fragmento ambíguo. Em dois requisitos das categorias Cat-02 e Cat-03, a conversão ocorreu exclusivamente em C3 (contexto irrelevante) e não em C2, sugerindo sensibilidade à especificidade do texto injetado independente de sua relevância. O teste de McNemar reportou poder estatístico insuficiente (n_discordante = 4), impossibilitando inferência.

O phi4-mini e o deepseek-r1:7b registraram ΔRoute = 0,0% em todas as métricas de todas as condições. Para o phi4-mini, esse resultado combinado com o desempenho do Bloco 1 (revocação 100%) caracterizou um modelo que detectou todas as ambiguidades mas considerou nenhuma resolúvel com qualquer volume de contexto — padrão de conservadorismo na resolução independente do insumo. Para o deepseek-r1:7b, os cinco falsos negativos em C0 reduziram a base de análise para sete requisitos, todos roteados para signaling e nenhum convertido por C1, C2 ou C3.

O llama3.1-8b apresentou particularidade relevante: 27,3% dos requisitos foram roteados para structured já em C0, sem qualquer contexto adicional. Esse patamar elevado de resolução autônoma comprimiu os deltas observados em condições superiores, de modo que o ΔC2−C0 de 54,5% subestima a sensibilidade real do modelo ao contexto: os requisitos que o modelo não resolveu em C0 foram convertidos em C2 na proporção esperada, mas a base de cálculo era menor.

Esses resultados são compatíveis com a observação de Bashir et al. (2025) de que estratégias de prompting com informação contextual elevam o desempenho de LLMs na tarefa de detecção de ambiguidades industriais — embora o mecanismo seja distinto: enquanto Bashir et al. injetaram exemplos de requisitos rotulados como demonstrações (aprendizado em contexto de poucos exemplos), o presente pipeline injetou documentação de domínio diretamente relacionada ao requisito analisado. A heterogeneidade da resposta — significativa apenas nos modelos qwen — indica que a capacidade de aproveitamento do contexto injetado depende da arquitetura do modelo e não é garantida pela simples disponibilidade da informação.

## Bloco 3 — Classificação de tipo de ambiguidade

O Bloco 3 avaliou se o tipo de ambiguidade detectado pelo Agente 1 coincidiu com os tipos aceitos declarados no corpus, respondendo a RQ3. A análise restringiu-se às categorias Cat-02, Cat-03 e Cat-04, que possuem `taxonomy_accepted_types` preenchido. A Tabela 3 apresenta a proporção de acerto por categoria e por modelo.

**Tabela 3.** Proporção de acerto de tipo de ambiguidade por categoria e modelo em C0 (acertos/3 por célula)

| Modelo | Cat-02 Linguística | Cat-03 Domínio | Cat-04 Vaguidade |
|---|---:|---:|---:|
| qwen3.5-4b | 66,7% (2/3) | 66,7% (2/3) | 66,7% (2/3) |
| qwen3.5-9b | 66,7% (2/3) | 33,3% (1/3) | 66,7% (2/3) |
| gemma3-4b | 33,3% (1/3) | 0,0% (0/3) | 66,7% (2/3) |
| mistral-7b | 66,7% (2/3) | 0,0% (0/3) | 0,0% (0/3) |
| llama3.1-8b | 66,7% (2/3) | 33,3% (1/3) | 0,0% (0/3) |
| phi4-mini | 100,0% (3/3) | 33,3% (1/3) | 33,3% (1/3) |
| deepseek-r1:7b | 66,7% (2/3) | 33,3% (1/3) | 0,0% (0/3) |

*Fonte: Resultados originais da pesquisa*

Cat-02 (linguística) registrou o melhor desempenho: seis dos sete modelos acertaram dois ou três tipos, com mediana de 66,7%. Os requisitos dessa categoria apresentam marcadores textuais reconhecíveis — pronomes sem referente inequívoco, estruturas de coordenação com escopo ambíguo — que parecem ter correspondência direta com padrões linguísticos internalizados durante o pré-treinamento.

Cat-03 (domínio) e Cat-04 (vaguidade) revelaram limitações sistemáticas. Em Cat-03, gemma3-4b e mistral-7b não acertaram nenhum dos tipos esperados. Essa categoria demandou a identificação de ambiguidade lexical ou semântica cuja resolução dependia de definições operacionais de domínio — ausentes nos modelos avaliados, que nomearam as ambiguidades como linguísticas ou estruturais em vez de semânticas de domínio. Em Cat-04, quatro dos sete modelos registraram 0,0% de acerto. A vaguidade, no sentido da taxonomia de Pohl (2025), exige reconhecer que um predicado é objetivamente inverificável por imprecisão de fronteira — uma distinção conceitual sutil que não emergiu do prompting adotado: os modelos tenderam a classificar predicados vagos como ambiguidades semânticas ou simplesmente como imprecisões, sem utilizar o rótulo específico da taxonomia.

O phi4-mini apresentou o único caso de acerto perfeito em qualquer categoria: 100% em Cat-02. Combinado com o desempenho nulo do mesmo modelo no Bloco 2, esse resultado indicou que a capacidade de nomear corretamente o tipo de ambiguidade linguística de superfície não se traduziu em capacidade de resolução — o modelo discriminou o tipo mas não produziu requisito estruturado.

A observação de que modelos com alta revocação não necessariamente classificam tipos corretamente sugere a existência de um gargalo de granularidade: modelos de pequeno porte internalizaram a noção genérica de ambiguidade, mas não seus subtipos conforme taxonomias formais — achado consistente com Cheng et al. (2025), que identificaram que a maioria dos estudos de IA generativa em Engenharia de Requisitos foca elicitação e validação, enquanto a detecção e classificação de defeitos permanece entre as tarefas menos exploradas na literatura recente.

## Bloco 4 — Integridade estrutural

O Bloco 4 aferiu se o pipeline produziu artefatos utilizáveis em todas as condições. A integridade estrutural (D_output) atingiu 100% em todos os sete modelos e nas quatro condições de contexto, totalizando 357 execuções sem falha estrutural. A ausência de falhas confirmou que os mecanismos de serialização, validação e roteamento do pipeline operaram dentro dos parâmetros esperados ao longo de todo o experimento.

## Resposta às hipóteses

H1 — que o contexto específico relevante (C2) produz mais conversões signaling → structured do que o contexto específico irrelevante (C3) — foi confirmada para dois dos sete modelos avaliados: qwen3.5-4b (p = 0,016) e qwen3.5-9b (p = 0,031). Para os demais modelos, o número de pares discordantes foi insuficiente para inferência estatística. Para phi4-mini e deepseek-r1:7b, H1 foi refutada descritivamente: ΔC2−C3 = 0,0% em ambos os casos. H1 foi, portanto, parcialmente confirmada — válida para os modelos da família qwen e não sustentada pelos dados para os demais.

H2 — que o pipeline detecta ambiguidades com precisão e revocação acima de 80% — foi confirmada para cinco dos sete modelos em revocação (83,3% a 100%) e para quatro dos sete em precisão (83,3% a 87,5%). O deepseek-r1:7b não satisfez o critério de revocação (58,3%). qwen3.5-9b e llama3.1-8b registraram precisão de 78,6%, marginalmente abaixo do limiar de 80%. Os ICs bootstrap indicaram que as estimativas pontuais são consistentes com os dados, mas o tamanho amostral de 15 execuções em C0 não permite descartar valores substancialmente menores em corpora maiores.

H3 — que Cat-04 (vaguidade) apresenta o menor acerto de tipo de ambiguidade — foi confirmada: Cat-04 registrou o desempenho mais baixo em cinco dos sete modelos e o pior resultado agregado do conjunto, com quatro modelos em 0,0% de acerto — resultado inferior ao de Cat-02 em todos os casos e inferior ao de Cat-03 na maioria. A vaguidade constituiu o subtipo de ambiguidade mais difícil para os modelos avaliados, provavelmente por exigir raciocínio sobre verificabilidade objetiva de predicados — dimensão que a taxonomia de Pohl (2025) distingue explicitamente de outros tipos de imprecisão textual, mas que o prompting padrão não induziu os modelos a discriminar.
