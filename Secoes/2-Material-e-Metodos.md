# Material e Métodos

## Delineamento da pesquisa

Esta pesquisa foi classificada como aplicada, de abordagem quantitativa e objetivo explicativo (Gil, 2018): buscou identificar o efeito do nível e da relevância do contexto fornecido a um "pipeline" multi-agente sobre a resolução de ambiguidades em requisitos de software, isto é, sobre a rota de resolução adotada. Complementarmente, descreveu o desempenho do "pipeline" na detecção e na classificação de tipo, etapas independentes do contexto, avaliadas na condição sem contexto (C0). O delineamento foi experimental (Kerlinger, 1980), com manipulação da variável independente — a condição de contexto — e mensuração das dependentes em condições controladas.

O objeto de estudo foi o "pipeline" multi-agente de detecção e resolução de ambiguidades, implementado pelo autor e aplicado a um corpus controlado de 15 requisitos. A coleta foi documental (Gil, 2018): os requisitos foram extraídos de publicações científicas e tratados como dados — os textos, e não as análises dos autores das fontes —, sem participantes humanos. O instrumento foi o próprio "pipeline", que registrou a cada execução um artefato de saída (`final_output.json`), consolidado em métricas pelo script `evaluate.py`.

Não houve trabalho de campo: o autor conduziu a pesquisa em ambiente computacional local (subseção Modelos e parâmetros de execução). O primeiro registro de desenvolvimento no repositório do estudo foi feito em 30 de maio de 2026; a execução-piloto ocorreu em 29 de julho e o experimento principal, em 22 e 23 de setembro. Por não envolver participantes humanos nem dados pessoais, e por utilizar apenas textos públicos de publicações científicas, a pesquisa não foi submetida a Comitê de Ética em Pesquisa (Brasil, 2016).

Os sujeitos do experimento foram os requisitos, e a população de referência, o conjunto de requisitos de software em linguagem natural em inglês. Como a seleção dos 15 requisitos foi intencional (subseção Corpus controlado), os resultados não puderam ser generalizados estatisticamente a essa população. Em contrapartida, cada requisito foi submetido a todas as condições e serviu de controle de si mesmo, com comparações pareadas, o que dispensou a randomização: não havia grupos distintos cujas características pudessem confundir os resultados.

As chamadas ao modelo foram independentes entre si, cada uma enviada sem o histórico das anteriores. A única dependência deliberada foi o reaproveitamento da saída do Agente 1, obtida uma vez por requisito e compartilhada pelas quatro condições (subseção Arquitetura do pipeline), o que reforçou o pareamento entre elas.

## Perguntas de pesquisa, hipóteses e operacionalização das variáveis

### Perguntas de pesquisa e hipóteses

Formularam-se três perguntas de pesquisa (do inglês "research questions" [RQ]) que orientaram o delineamento experimental. Os termos relativos ao corpus (categorias Cat-01 a Cat-05 e condições de contexto C0 a C3), ao "pipeline" (agentes e rotas de resolução) e à avaliação (métricas e blocos) foram detalhados nas subseções Corpus controlado, Arquitetura do pipeline e Protocolo de avaliação.

**RQ1:** A relevância semântica do contexto injetado — mantida a especificidade constante entre as condições C2 (contexto relevante) e C3 (contexto irrelevante) — altera a rota de resolução adotada pelo "pipeline"?

**RQ2:** O "pipeline" distingue requisitos ambíguos de requisitos bem formados, com precisão, revocação, F1 e especificidade adequadas, medidas sobre um grupo de controle negativo composto por requisitos selecionados da literatura sem defeitos esperados?

**RQ3:** Entre as categorias de ambiguidade — linguística, de domínio e de vaguidade —, quais apresentam maior dificuldade de classificação de tipo pelo "pipeline", segundo a taxonomia de Pohl (2025)? A categoria estrutural (Cat-01) integrou a detecção (RQ2), mas não a análise de tipo, pois seus defeitos não constituíram tipos dessa taxonomia.

A partir dessas perguntas, foram enunciadas três hipóteses experimentais.

**H1:** Se o contexto injetado for semanticamente relevante para o fragmento ambíguo (condição C2), então a taxa de conversão de rota `signaling→structured` será significativamente superior à observada quando o contexto for específico, porém irrelevante (condição C3), segundo teste exato binomial unilateral sobre os pares discordantes de cada modelo, com nível nominal α = 0,05 e critério de decisão corrigido para comparações múltiplas (subseção Análise estatística).

**H2:** Se o "pipeline" operar sobre o corpus controlado, então a precisão, a revocação e o F1 serão superiores a 0,70 nas execuções em C0, e a taxa de falsos positivos sobre Cat-05 será inferior a 0,30.

**H3:** Se o "pipeline" processar requisitos de categorias de defeito distintas, então, em cada modelo, a taxa de acerto de tipo na condição C0 variará entre Cat-02 (linguística), Cat-03 (de domínio) e Cat-04 (vaguidade).

Os limiares de H2 foram fixados antes da execução do experimento principal — registrados no repositório do estudo em 21 de setembro de 2026 (Andrade, 2026), um dia antes das execuções — como critério do pesquisador, e não como padrão normativo, dada a inexistência de valor de referência consolidado para a tarefa. O limiar de 0,30 para falsos positivos correspondeu ao complemento de uma especificidade de 0,70, mantendo a simetria com os demais critérios.

O valor de 0,70 situou-se na faixa de desempenho reportada por estudos anteriores: Bashir et al. (2025) obtiveram F1 de até 75,8% na detecção de ambiguidade em requisitos industriais com modelos de código aberto, e Nair e Anish (2025) reportaram revocação macro-média máxima de 0,76, obtida pelo GPT-4o-mini, modelo proprietário, e igualada pelo Qwen2.5-7B, de código aberto, em um dos dois documentos.

### Operacionalização das variáveis

A variável independente (VI) correspondeu à condição de contexto, operacionalizada em quatro níveis mutuamente exclusivos: C0 (sem contexto), C1 (domínio do sistema e glossário periférico), C2 (C1 acrescido de conteúdo diretamente relevante ao fragmento ambíguo) e C3 (C1 acrescido de conteúdo específico sobre aspecto distinto do fragmento ambíguo). O pesquisador a manipulou por meio da construção controlada do campo `context` em cada instância experimental do corpus.

Mediram-se três variáveis dependentes (VD). A VD1 foi a rota do "pipeline" — `structured` ou `signaling` —, derivada do campo `pipeline_decision.route` de `final_output.json`. A VD2 compreendeu as métricas de detecção — precisão, revocação, F1 e especificidade —, calculadas pelo `evaluate.py` a partir da classificação de cada execução em C0 como verdadeiro positivo [TP], falso positivo [FP], falso negativo [FN] ou verdadeiro negativo [TN]. A VD3 foi o acerto de tipo — binária por instância —, verificado pela presença de ao menos um dos tipos detectados entre os aceitos no corpus (`taxonomy_accepted_types`), em C0 de Cat-02, Cat-03 e Cat-04.

As variáveis controladas incluíram o texto do requisito (fixo por instância em todas as condições), a temperatura dos modelos (0,0 em todos os casos), o parâmetro `think: false` e o esquema dos "prompts" de sistema, em formato YAML Ain't Markup Language [YAML]. Os sete modelos não foram tratados como variável controlada, mas como réplicas do mesmo experimento, analisadas separadamente e comparadas entre si: suas diferenças de arquitetura, tamanho e treinamento não foram isoladas e limitaram a atribuição de diferenças de desempenho a características específicas dos modelos.

Reconheceram-se ainda como limitações do estudo: o não-determinismo residual das saídas, pois a temperatura 0,0 não garante determinismo bit a bit em execução por unidade de processamento gráfico [GPU]; o corpus reduzido, com três requisitos por categoria; o idioma único dos requisitos; o gabarito elaborado por um único anotador, sem medida formal de concordância; e a falha de conversão de três execuções do qwen3.5:9b, descrita em Resultados e Discussão.

## Corpus controlado

Para assegurar reprodutibilidade, construiu-se um corpus de 15 requisitos em linguagem natural, todos com fonte identificada na literatura e selecionados intencionalmente pelo autor, precedido por uma execução-piloto com seis requisitos construídos pelo autor.

### Execução-piloto

A execução-piloto foi realizada em julho de 2026, com o qwen3.5:9b, sobre seis requisitos construídos pelo autor, um por tipo de defeito, para exercitar cada categoria antes de definir o corpus final: um estrutural (ação funcional e critério de qualidade na mesma sentença); um referencial (pronome com dois antecedentes); um de vaguidade (critério de elegibilidade impreciso); um lexical (termo polissêmico); um semântico (precedência ambígua entre "e" e "ou"); e um de controle, sem ambiguidade. O piloto não integrou a avaliação; orientou o ajuste dos "prompts" dos agentes e a definição das categorias.

### Taxonomia de ambiguidades

A classificação adotou a taxonomia de Pohl (2025), com cinco tipos: **(1) lexical**, quando um termo admite múltiplos significados e o contexto não indica qual se aplica; **(2) sintática**, quando a estrutura gramatical admite mais de uma árvore de análise; **(3) semântica**, quando operadores lógicos ou relacionais — "e", "ou", "se" — não delimitam as condições a que se aplicam; **(4) referencial**, quando um pronome, anáfora ou expressão nominal tem mais de um antecedente plausível; e **(5) vaguidade**, quando predicados, quantificadores ou termos de fronteira impedem a verificação objetiva do critério.

A taxonomia orientou o gabarito e os "prompts" do Agente 1, o que tornou comparáveis os tipos detectados e os declarados manualmente.

### Categorias do corpus

Os 15 requisitos foram distribuídos em cinco categorias: **(Cat-01) estrutural**, com defeitos de formação — não-factibilidade, não-atomicidade e incompletude —, referenciados nos "requirement smells" de Veizaga et al. (2024) e nos critérios de qualidade de Pohl (2025); **(Cat-02) linguística**, com ambiguidades sintáticas, referenciais e semânticas (de operadores lógicos), independentes de conhecimento de domínio; **(Cat-03) de domínio**, com ambiguidades lexicais e semânticas cuja resolução dependia de conhecimento especializado ou de definições operacionais ausentes; **(Cat-04) de vaguidade**, com quantificadores, termos de fronteira ou predicados temporais imprecisos (Pohl, 2025); e **(Cat-05) de controle**, com requisitos intencionalmente bem formados e sem defeitos esperados.

Os três requisitos de Cat-05 constituíram o grupo de controle negativo, selecionado da literatura por não apresentar ambiguidades nem defeitos estruturais. Sua função foi verificar se o "pipeline" alertava para ambiguidade na ausência de defeitos reais, condição necessária para interpretar as demais categorias. O grupo funcionou, assim, como sonda de falsos positivos: mediu a taxa-base de detecções indevidas do Agente 1, tratada como achado do estudo, e não como pressuposto de desempenho sem alertas.

Como limitação de desenho, os três requisitos de Cat-05 representaram 20% do corpus e foram escolhidos intencionalmente pelo autor, não por amostragem aleatória, o que foi considerado na interpretação dos índices de falsos positivos em Resultados e Discussão.

### Seleção dos requisitos

Os requisitos do corpus final foram selecionados intencionalmente pelo autor, e não por amostragem aleatória, a partir de exemplos publicados na literatura (Bashir et al., 2025; Kamsties et al., 2001; Pohl, 2025; Unterbusch e Vogelsang, 2026; Veizaga et al., 2024; Vogelsang et al., 2025). O professor orientador revisou a seleção, e cada requisito manteve a citação de origem, o que permitiu rastrear o defeito esperado até a fonte. Adotaram-se três requisitos por categoria, em um desenho balanceado de 15 textos-base.

O tamanho respondeu também a uma restrição prática: o experimento foi executado em um único equipamento de uso individual — um MacBook Pro com chip Apple M5 e 16 GB de memória de acesso aleatório [RAM] —, e o tempo de execução cresceria proporcionalmente ao número de requisitos. Cada requisito adicional acrescentaria sete execuções em C0 (uma por modelo) e, se detectado, outras 21 em C1, C2 e C3 (sete modelos × três condições), além de repetições em caso de falha. Manteve-se, assim, um corpus enxuto.

### Condições de contexto

Cada requisito foi avaliado sob quatro condições de contexto: C0 (sem contexto); C1 (domínio do sistema e glossário de termos periféricos, excluindo o fragmento ambíguo); C2 (C1 acrescido de conteúdo que endereça diretamente o fragmento ambíguo, na forma de definição operacional, regra de negócio ou restrição); e C3 (C1 acrescido de conteúdo específico sobre um aspecto diferente do requisito, nunca o fragmento ambíguo).

O delineamento teve um único fator manipulado — a condição de contexto —, com quatro níveis (Wohlin et al., 2012), replicado nos sete modelos e analisado separadamente em cada um. Não foi um plano fatorial completo: C1, C2 e C3 diferiram em especificidade (baixa ou alta) e relevância (irrelevante ou relevante), mas a combinação de baixa especificidade com relevância não foi construída. Contrastes planejados, pareados por requisito, isolaram cada efeito: C2 vs. C3, o da relevância com especificidade constante (alta); C3 vs. C1, o da especificidade com relevância constante (nula); e C1 vs. C0, o do contexto genérico.

C0 foi executado para todos os requisitos; C1, C2 e C3, apenas quando o Agente 1 detectou ambiguidade em C0, inclusive nos de Cat-05, em que a detecção constituiu falso positivo, mas acionou as condições seguintes; a não detecção dispensou as três. Das 60 instâncias experimentais possíveis (15 textos-base × 4 condições), só as 15 de C0 foram executadas incondicionalmente. Sobre os sete modelos (subseção Modelos e parâmetros de execução), o teto foi de 420 execuções (60 × 7); o número efetivo dependeu das detecções de cada modelo e foi reportado em Resultados e Discussão.

A distinção entre texto-base — o requisito selecionado — e instância experimental — a combinação de requisito e condição de contexto — evitou ambiguidade metodológica ao reportar os resultados. O corpus está descrito no Apêndice A e disponível em Andrade (2026).

### Gabarito de avaliação

Para Cat-02, Cat-03 e Cat-04, cujas ambiguidades eram classificáveis na taxonomia de Pohl (2025), o corpus definiu o campo `taxonomy_accepted_types`, lista dos tipos esperados elaborada pelo autor e validada pelo professor orientador. Cat-01 não teve o campo, pois seus defeitos de formação — não-factibilidade, não-atomicidade e incompletude — não constituíram tipos dessa taxonomia. A elaboração por um único anotador, com validação do orientador e sem medida formal de concordância, constituiu limitação do estudo.

O gabarito de detecção derivou da categoria do requisito: Cat-01 a Cat-04 foram positivos e Cat-05, o grupo de controle negativo. O tipo detectado pelo Agente 1 foi confrontado com `taxonomy_accepted_types` no Bloco 3 (subseção Protocolo de avaliação), restrito às três categorias que tiveram o campo.

### Idioma

Os requisitos foram mantidos no idioma original das fontes, o inglês, para preservar os fenômenos linguísticos analisados, pois a tradução poderia introduzir ou eliminar ambiguidades ausentes do texto original. Estudos recentes indicaram forte influência do inglês nos espaços representacionais e na naturalidade das saídas de modelos multilíngues em outros idiomas (Guo et al., 2025; Schut et al., 2025) e que tarefas traduzidas não capturaram adequadamente as nuances do português brasileiro (Almeida et al., 2025). Como delimitação, os resultados referiram-se a requisitos em inglês.

## Modelos e parâmetros de execução

Os experimentos usaram sete modelos de código aberto, executados localmente via Ollama (Ollama, 2026): `qwen3.5:4b`, `qwen3.5:9b`, `gemma3:4b`, `mistral:7b`, `llama3.1:8b`, `phi4-mini` e `deepseek-r1:7b`. A execução local eliminou a variabilidade de atualizações de interface de programação de aplicações [API] e favoreceu a reprodutibilidade.

As execuções ocorreram em 22 e 23 de setembro de 2026, em um MacBook Pro com chip Apple M5 e 16 GB de RAM, sob macOS 27.0 e Ollama 0.21.1. Todos os modelos usaram a quantização Q4_K_M distribuída pelo Ollama, janela de contexto (`num_ctx`) de 8.192 tokens e limite de geração (`num_predict`) de 2.500 a 3.000 tokens, conforme o agente.

A `seed` não foi fixada explicitamente: com temperatura 0,0, a amostragem foi determinística, e a semente, que controla apenas a amostragem, não influenciou a escolha dos tokens; o não-determinismo residual de origem numérica independeu dela. O ambiente, os parâmetros e as impressões digitais ("digests") dos arquivos dos modelos estão registrados em Andrade (2026). A versão do Ollama e o equipamento foram registrados após as execuções, e não por execução, o que limitou a rastreabilidade.

Os sete modelos foram selecionados segundo quatro critérios: (1) pesos abertos no repositório do Ollama, que permitiram a execução local e reprodutível; (2) porte entre 3,8 e 9,7 bilhões de parâmetros, compatível com o equipamento; (3) diversidade de famílias e fornecedores — Qwen, Gemma, Mistral, Llama, Phi e DeepSeek —, para reduzir o risco de que os achados refletissem idiossincrasias de uma única arquitetura ou base de treinamento; e (4) variação intencional de porte e de modo de raciocínio.

Quanto ao quarto critério, dois tamanhos da mesma família (`qwen3.5:4b` e `qwen3.5:9b`) permitiram observar o efeito de escala com a arquitetura constante, e a inclusão de modelos com raciocínio interno (`qwen3.5` e `deepseek-r1:7b`) ao lado de modelos sem esse recurso permitiu comparar os dois perfis sob o mesmo protocolo.

Todos os modelos foram configurados com temperatura 0,0, que eliminou a amostragem estocástica e produziu a sequência de tokens de maior probabilidade a cada passo. A configuração reduz, mas não elimina, o não-determinismo residual — decorrente, por exemplo, de técnicas de eficiência computacional e de aritmética de ponto flutuante —, observado em estudos empíricos mesmo em configurações ditas determinísticas (Atil et al., 2024; Ouyang et al., 2024). A reprodutibilidade foi, por isso, tratada como reprodutibilidade de configuração, e não como identidade bit a bit das saídas.

O parâmetro `think` foi definido como `false` e enviado a todos os modelos pela interface de transferência de estado representacional [REST] do Ollama. Nos modelos com raciocínio interno — `qwen3.5:4b`, `qwen3.5:9b` e `deepseek-r1:7b` —, buscou desabilitar o encadeamento de pensamento, de modo que a saída fosse diretamente o documento YAML especificado no "prompt" de cada agente. A desabilitação não foi absoluta em todas as execuções (Resultados e Discussão); nos demais modelos (`gemma3:4b`, `mistral:7b`, `llama3.1:8b` e `phi4-mini`), o servidor ignorou o parâmetro sem consequências.

## Arquitetura do pipeline

O "pipeline" foi composto por três agentes LLM especializados e um consolidador em Python (Figura 1), com uma única responsabilidade por agente (Gulli, 2025). A orquestração foi implementada diretamente em Python, sem "frameworks" como LangChain ou LangGraph, dado o caráter sequencial e determinístico do "pipeline", cujas entradas e saídas seguiram esquemas YAML fixos que dispensaram abstrações adicionais.

![](arquitetura-pipeline.svg)

Figura 1. Arquitetura do "pipeline" multi-agente: fluxo do requisito pelo Agente 1, pelo Agente 2, pelo Agente 3 e pelo consolidador, com as rotas `structured` e `signaling`

*Fonte: Dados originais da pesquisa*

O Agente 1 recebeu exclusivamente o texto do requisito (`base_requirement_text`), sem contexto, glossário ou metadados, identificou os fragmentos com mais de uma interpretação e os classificou segundo a taxonomia de Pohl (2025), produzindo o atributo `has_ambiguity`. Por ser independente do contexto, executou uma vez por requisito, e sua saída foi reutilizada nas quatro condições (C0–C3, definidas na subseção Corpus controlado).

Quando `has_ambiguity` era falso, o orquestrador substituiu o Agente 2 por um bloco sintético determinístico, com status `no_ambiguity`, e encaminhou o requisito ao Agente 3. Quando era verdadeiro, o Agente 2 recebeu o requisito, o contexto da condição em curso e a saída do Agente 1, e atribuiu a cada ambiguidade um de três status: `resolvable`, com evidência suficiente no texto ou no contexto para selecionar uma interpretação; `unresolved`, com informação insuficiente para resolvê-la; ou `false_positive`, quando as evidências mostraram que uma ou mais interpretações candidatas não tinham base no texto e a ambiguidade não se sustentava.

O status global foi `fully_resolvable`, quando todas as ambiguidades eram `resolvable` ou `false_positive`, ou `unresolved`, quando ao menos uma permaneceu sem resolução. O bloco sintético recebeu o status global `no_ambiguity`, tratado no roteamento como equivalente a `fully_resolvable`.

Requisitos `fully_resolvable` ou `no_ambiguity` seguiram pela rota `structured` até o Agente 3; os `unresolved` seguiram pela rota `signaling`, que encerrou o "pipeline" sem invocá-lo e deixou a ambiguidade aberta para intervenção humana. O Agente 3 recebeu o texto do requisito e a saída do Agente 2 e produziu o requisito estruturado, classificado como funcional, de qualidade ou restrição (Pohl, 2025): fragmentos `resolvable` foram substituídos pela interpretação suportada no `final_statement`, e requisitos `false_positive` mantiveram o texto original.

O consolidador, um script Python determinístico, integrou as saídas dos três agentes e a decisão de roteamento em um único artefato por execução (`final_output.json`), inclusive nos casos `signaling`, cujo registro compôs os dados de análise. As execuções interrompidas por falha de conversão da resposta do modelo em YAML não chegaram a ele nem geraram artefato (subseção Protocolo de avaliação). O código-fonte completo e os "prompts" de sistema dos agentes, no diretório `Agents/`, estão disponíveis em Andrade (2026).

## Protocolo de avaliação

A avaliação quantitativa comparou, para cada execução, os campos da saída do "pipeline" com um gabarito derivado do corpus, integralmente pelo script `evaluate.py`, que percorreu os arquivos `final_output.json` sem intervenção humana na classificação. O gabarito de detecção foi derivado diretamente do campo `category_id`, e não de `taxonomy_accepted_types`, ausente em Cat-01, o que causaria sua classificação incorreta como controle.

A avaliação foi organizada em quatro blocos, correspondentes às três perguntas de pesquisa e a uma verificação complementar de integridade.

### Bloco 1 — Detecção de ambiguidade

O Bloco 1 mediu a detecção de ambiguidade pelo Agente 1, respondendo a RQ2. Por ser a etapa "context-free" do "pipeline", utilizou apenas as execuções em C0, 15 instâncias por modelo. Cada instância foi classificada em TP, FP, FN ou TN, e desses contadores calcularam-se precisão, revocação, F1 e especificidade (Sokolova e Lapalme, 2009).

### Bloco 2 — Sensibilidade ao contexto

O Bloco 2 rastreou a rota do "pipeline" (`structured` ou `signaling`) nas quatro condições de contexto, respondendo a RQ1. A métrica central foi ΔRoute(C2 − C0), que indicou se o contexto específico relevante converteu a rota; ΔRoute(C3 − C0), Δ(C2 − C3) e Δ(C3 − C1) isolaram, respectivamente, o efeito do contexto específico irrelevante, o ganho puro de relevância com especificidade constante e o ganho puro de especificidade com relevância constante (nula).

Para cada modelo, reportou-se a média de cada ΔRoute sobre os requisitos considerados, isto é, a proporção de conversões `signaling→structured` descontada a de reversões, complementada pelos ganhos por etapa (C0→C1 e C1→C2). Sem gabarito de rota esperada por condição, essas métricas descreveram a rota adotada, sem julgá-la correta ou incorreta; a inferência sobre C2 versus C3 foi tratada na subseção Análise estatística.

### Bloco 3 — Classificação de tipo de ambiguidade

O Bloco 3 respondeu a RQ3: verificou se o tipo de ambiguidade detectado pelo Agente 1 coincidiu com os tipos aceitos no corpus, segundo a taxonomia de Pohl (2025) (subseção Taxonomia de ambiguidades). Restringiu-se a Cat-02, Cat-03 e Cat-04, que possuíam `taxonomy_accepted_types`, com a execução em C0. O acerto exigiu ao menos um tipo detectado entre os aceitos, pois o corpus admitia conjuntos alternativos para requisitos em que mais de um tipo era defensável.

### Bloco 4 — Integridade estrutural

O Bloco 4 foi uma verificação complementar de integridade estrutural da saída do "pipeline", independente das perguntas de pesquisa: avaliou se o "pipeline" produziu um artefato utilizável em todas as condições. Na rota `structured`, exigiu-se ao menos um item em `structured_requirements` com `final_statement` não vazio; na `signaling`, ao menos um item em `ambiguity_resolubility` com `resolubility_status` igual a `unresolved`, `non_resolvable` ou `false_positive`, desfechos válidos quando o "pipeline" não estruturou o requisito. Saídas com rota desconhecida receberam valor nulo e foram excluídas do denominador.

As execuções sem `final_output.json`, por falha na conversão da resposta do modelo em YAML, não integraram o indicador, por não haver artefato a avaliar; foram contadas e descritas à parte, com os registros de investigação preservados no repositório do estudo (Andrade, 2026), e retomadas em Resultados e Discussão.

### Análise estatística

A análise estatística foi implementada no script `evaluate.py` e registrada no repositório do estudo em 21 de setembro de 2026 (Andrade, 2026), antes das execuções de 22 e 23 de setembro, com nível de significância α = 0,05 como referência dos testes inferenciais.

Em RQ1, a unidade de análise foi o par C2/C3 de cada requisito com ambiguidade detectada em C0, únicos casos em que C1 a C3 foram executadas. Os pares incluíram os requisitos de Cat-05 detectados (falsos positivos), ao passo que as proporções descritivas do Bloco 2 consideraram apenas Cat-01 a Cat-04.

A conversão `signaling→structured` em uma condição Cx foi registrada por ΔRoute(Cx − C0) = +1, e a taxa de conversão foi a proporção de requisitos convertidos. Como ΔRoute(C2 − C3) = ΔRoute(C2 − C0) − ΔRoute(C3 − C0), o teste sobre os pares discordantes de rota em C2 e C3 equivale ao teste sobre a diferença entre as conversões nas duas condições.

A comparação entre C2 e C3 foi feita por modelo, com teste exato binomial unilateral sobre os pares discordantes — equivalente ao teste de McNemar (1947) exato unilateral —, sob H1: C2 > C3. O teste só foi aplicado com ao menos cinco pares discordantes: com quatro ou menos, o menor valor de p unilateral possível (0,0625) excede α = 0,05, e com cinco, todos favoráveis a C2, p = 0,031. Nos demais modelos, a comparação foi descritiva. Com no máximo 15 pares por modelo, os resultados foram reportados com a ressalva de baixo poder estatístico.

Como a análise de RQ1 envolveu um teste por modelo, adotou-se como critério principal a correção de Bonferroni (Dunn, 1961) sobre os sete modelos, tomados como a família de comparações (α ajustado = 0,05/7 ≈ 0,007). Sob esse limiar, o teste só rejeitaria a hipótese nula com ao menos oito pares discordantes, todos favoráveis a C2: com sete, o menor valor de p possível (0,0078) excede 0,007. Essa correção não integrou o planejamento original e foi incorporada posteriormente, em postura conservadora.

Como referência menos conservadora, aplicou-se também a correção de Holm-Bonferroni (Holm, 1979) apenas sobre os testes efetivamente conduzidos. Os resultados de RQ1 foram, portanto, interpretados como evidência exploratória, e a significância ao nível nominal de 0,05 foi reportada como indício, e não como confirmação.

Em RQ2, os intervalos de confiança [IC] de 95% para precisão, revocação, F1 e especificidade foram estimados por modelo com "bootstrap" percentil (limites de 2,5% e 97,5%), 10.000 reamostras dos pares (gabarito, detecção) das 15 execuções em C0 e semente 42, método que não pressupõe distribuição normal (Efron e Hastie, 2016). Reamostras com métrica indefinida foram descartadas: na especificidade, as sem nenhum requisito de Cat-05, o que deixou 9.641 das 10.000 válidas. Dado o tamanho da amostra, os intervalos indicaram a incerteza, sem constituir estimativas precisas.

A hipótese H2 foi avaliada por modelo, comparando as estimativas pontuais em C0 aos limiares de 0,70 (precisão, revocação e F1) e 0,30 (taxa de falsos positivos), sem agregação entre modelos; os IC complementaram a leitura. Como Cat-05 continha apenas três requisitos, a taxa de falsos positivos só pôde assumir os valores 0, 0,33, 0,67 ou 1, de modo que o limiar de 0,30 equivaleu, na prática, à exigência de nenhum falso positivo, e a especificidade teve resolução igualmente grosseira.

Em RQ3, o acerto de tipo entre categorias foi reportado por proporção (acertos/3 por categoria e modelo), sem teste inferencial, pois três requisitos por categoria não bastam para um teste de associação com poder interpretável. A H3 foi lida por modelo, comparando Cat-02, Cat-03 e Cat-04: contou-se em quantos modelos as três proporções diferiram e, em cada um, quais categorias tiveram o maior e o menor acerto, de forma descritiva. Os resultados foram apresentados em tabela de frequências que cruza categoria, modelo e condição C0.
