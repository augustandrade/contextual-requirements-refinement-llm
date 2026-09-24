# Perguntas de pesquisa, hipóteses e operacionalização das variáveis

<!-- Posicionamento: subtópico de abertura da seção Material e Métodos.
     Ordem das subseções: perguntas de pesquisa (este arquivo) → corpus controlado → modelos e parâmetros → arquitetura do pipeline → protocolo de avaliação. -->

Esta pesquisa foi classificada como de natureza aplicada, com abordagem quantitativa e objetivo explicativo (Gil, 2018): buscou identificar a relação causal entre o nível e a relevância do contexto fornecido a um "pipeline" multi-agente e os resultados de detecção e resolução de ambiguidades em requisitos de software. O delineamento adotado foi o experimental (Kerlinger, 1980), com manipulação direta da variável independente — condição de contexto — e mensuração das variáveis dependentes em condições controladas. A técnica de coleta de dados adotada foi a pesquisa documental (Gil, 2018): os requisitos que compuseram o corpus foram extraídos de publicações científicas e tratados como dados do estudo — os próprios textos dos requisitos, e não as análises dos autores das fontes —, sem coleta primária junto a participantes humanos.

O objeto de estudo foi o "pipeline" multi-agente de detecção e resolução de ambiguidades, implementado pelo autor — o que caracteriza também uma implementação de algoritmo —, aplicado a um corpus controlado de 15 requisitos. O instrumento de coleta de dados foi o próprio "pipeline", que registrou, a cada execução, um artefato de saída (`final_output.json`), posteriormente consolidado em métricas pelo script `evaluate.py`. Não houve trabalho de campo: a pesquisa foi conduzida pelo autor em ambiente computacional local, descrito na subseção Modelos e parâmetros de execução. O primeiro registro de desenvolvimento no repositório do estudo data de 30 de maio de 2026; a execução-piloto ocorreu em 29 de julho e o experimento principal, em 22 e 23 de setembro de 2026. Por não envolver participantes humanos nem dados pessoais, e por utilizar apenas textos de publicações científicas de acesso público, a pesquisa não foi submetida a Comitê de Ética em Pesquisa (Brasil, 2016).

**Perguntas de pesquisa e hipóteses**

Formularam-se três perguntas de pesquisa que orientaram o delineamento experimental. Os termos relativos ao corpus (categorias Cat-01 a Cat-05 e condições de contexto C0 a C3), ao "pipeline" (agentes e rotas de resolução) e à avaliação (métricas e blocos) são detalhados, respectivamente, nas subseções Corpus controlado, Arquitetura do pipeline e Protocolo de avaliação.

**RQ1:** A relevância semântica do contexto injetado — mantida a especificidade constante entre as condições C2 (contexto relevante) e C3 (contexto irrelevante) — altera a rota de resolução adotada pelo "pipeline"?

**RQ2:** O "pipeline" distingue requisitos ambíguos de bem formados sem gerar falsos positivos, mantendo precisão, revocação, F1 e especificidade adequadas sobre um grupo de controle intencionalmente construído sem defeitos?

**RQ3:** Entre as categorias de ambiguidade — linguística, de domínio e de vaguidade —, quais apresentam maior dificuldade de classificação de tipo pelo "pipeline", segundo a taxonomia de Pohl (2025)? A categoria estrutural (Cat-01) integra a detecção (RQ2), mas não a análise de tipo, pois seus defeitos não constituem tipos dessa taxonomia.

A partir dessas perguntas, foram enunciadas três hipóteses experimentais.

**H1:** Se o contexto injetado for semanticamente relevante para o fragmento ambíguo (condição C2), então a taxa de conversão de rota `signaling→structured` será significativamente superior à observada quando o contexto for específico, porém irrelevante (condição C3), segundo teste exato binomial unilateral sobre os pares discordantes de cada modelo (α = 0,05).

**H2:** Se o "pipeline" operar sobre o corpus controlado, então a precisão, a revocação e o F1 serão superiores a 0,70 nas execuções em C0, e a taxa de falsos positivos sobre Cat-05 será inferior a 0,30.

**H3:** Se as categorias de defeito diferirem em complexidade linguística e dependência de domínio, então Cat-03 (domínio) e Cat-04 (vaguidade) apresentarão menor taxa de acerto de tipo do que Cat-02 (linguística), na condição C0.

Os limiares de H2 foram fixados antes da execução do experimento como critério do pesquisador, e não como padrão normativo, dada a inexistência de valor de referência consolidado para a tarefa. O valor de 0,70 situou-se na faixa de desempenho reportada por estudos anteriores: Bashir et al. (2025) obtiveram F1 de até 75,8% na detecção de ambiguidade em requisitos industriais com modelos de código aberto, e Nair e Anish (2025) reportaram revocação macro-média máxima de 0,75, obtida pelo GPT-4o-mini, modelo proprietário. O limiar de 0,30 para falsos positivos corresponde ao complemento de uma especificidade de 0,70, mantendo a simetria com os demais critérios.

**Operacionalização das variáveis**

A variável independente (VI) correspondeu à condição de contexto experimental, operacionalizada em quatro níveis mutuamente exclusivos: C0 (sem contexto), C1 (domínio do sistema e glossário periférico), C2 (C1 acrescido de conteúdo diretamente relevante ao fragmento ambíguo) e C3 (C1 acrescido de conteúdo específico sobre aspecto distinto do fragmento ambíguo). A VI foi manipulada pelo pesquisador por meio da construção controlada do campo `context` em cada instância experimental do corpus.

Três variáveis dependentes foram mensuradas. A primeira (VD1) correspondeu à rota do "pipeline" — categórica binária: `structured` ou `signaling` —, derivada automaticamente do campo `routing_decision` do artefato `final_output.json`. A segunda (VD2) compreendeu as métricas de detecção — precisão, revocação, F1 e especificidade —, calculadas pelo script `evaluate.py` a partir das classificações TP, FP, FN e TN de cada execução em C0. A terceira (VD3) registrou o acerto de tipo de ambiguidade — variável binária por instância —, verificada pela presença de ao menos um dos tipos detectados pelo Agente 1 entre os tipos aceitos declarados no corpus (`taxonomy_accepted_types`), nas execuções em C0 de Cat-02, Cat-03 e Cat-04.

As variáveis controladas incluíram o texto do requisito (fixo por instância em todas as condições), a temperatura dos modelos (0,0 em todos os casos), o parâmetro `think: false` e o esquema YAML dos "prompts" de sistema. Os sete modelos avaliados foram tratados como fator de comparação, e não como variável controlada: suas diferenças arquiteturais, de tamanho e de treinamento não foram isoladas e limitam a atribuição de diferenças de desempenho a características específicas dos modelos. Reconhece-se ainda, como limitação, que a temperatura 0,0 não garante determinismo bit a bit em execução por GPU.
