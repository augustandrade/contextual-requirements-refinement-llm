# Perguntas de pesquisa, hipóteses e operacionalização das variáveis

<!-- Posicionamento: subtópico de abertura da seção Material e Métodos, antes da descrição do corpus. -->

Esta pesquisa foi classificada como de natureza aplicada, com abordagem quantitativa e objetivo explicativo (Gil, 2018): buscou identificar a relação causal entre o nível e a relevância do contexto fornecido a um "pipeline" multi-agente e os resultados de detecção e resolução de ambiguidades em requisitos de software. O delineamento adotado foi o experimental (Kerlinger, 1980), com manipulação direta da variável independente — condição de contexto — e mensuração das variáveis dependentes em condições controladas. A técnica de coleta de dados adotada foi a pesquisa documental (Gil, 2018): os requisitos que compuseram o corpus foram extraídos de publicações científicas e repositórios públicos, sem coleta primária junto a participantes humanos.

**Perguntas de pesquisa e hipóteses**

Formularam-se três perguntas de pesquisa que orientaram o delineamento experimental.

**RQ1:** A relevância semântica do contexto injetado — mantida a especificidade constante entre as condições C2 (contexto relevante) e C3 (contexto irrelevante) — altera a rota de resolução adotada pelo "pipeline"?

**RQ2:** O "pipeline" distingue requisitos ambíguos de bem formados sem gerar falsos positivos, mantendo precisão, revocação, F1 e especificidade adequadas sobre um grupo de controle intencionalmente construído sem defeitos?

**RQ3:** Quais categorias de defeito — estrutural, linguística, de domínio e de vaguidade — apresentam maior dificuldade de detecção e classificação pelo "pipeline", segundo a taxonomia de Pohl (2025)?

A partir dessas perguntas, foram enunciadas três hipóteses experimentais.

**H1:** Se o contexto injetado for semanticamente relevante para o fragmento ambíguo (condição C2), então a taxa de conversão de rota `signaling→structured` será significativamente superior à observada quando o contexto for específico, porém irrelevante (condição C3).

**H2:** Se o "pipeline" operar sobre o corpus controlado, então a precisão, a revocação e o F1 serão superiores a 0,70 nas execuções em C0, e a taxa de falsos positivos sobre Cat-05 será inferior a 0,30.

**H3:** Se as categorias de defeito diferirem em complexidade linguística e dependência de domínio, então Cat-03 (domínio) e Cat-04 (vaguidade) apresentarão menor taxa de acerto de tipo do que Cat-02 (linguística), na condição C0.

**Operacionalização das variáveis**

A variável independente (VI) correspondeu à condição de contexto experimental, operacionalizada em quatro níveis mutuamente exclusivos: C0 (sem contexto), C1 (domínio do sistema e glossário periférico), C2 (C1 acrescido de conteúdo diretamente relevante ao fragmento ambíguo) e C3 (C1 acrescido de conteúdo específico sobre aspecto distinto do fragmento ambíguo). A VI foi manipulada pelo pesquisador por meio da construção controlada do campo `context` em cada instância experimental do corpus.

Três variáveis dependentes foram mensuradas. A primeira (VD1) correspondeu à rota do "pipeline" — categórica binária: `structured` ou `signaling` —, derivada automaticamente do campo `routing_decision` do artefato `final_output.json`. A segunda (VD2) compreendeu as métricas de detecção — precisão, revocação, F1 e especificidade —, calculadas pelo script `evaluate.py` a partir das classificações TP, FP, FN e TN de cada execução em C0. A terceira (VD3) registrou o acerto de tipo de ambiguidade — variável binária por instância —, verificada pela presença de ao menos um dos tipos detectados pelo Agente 1 entre os tipos aceitos declarados no corpus (`taxonomy_accepted_types`), nas execuções em C0 de Cat-02, Cat-03 e Cat-04.

As variáveis controladas incluíram o texto do requisito (fixo por instância em todas as condições), a temperatura dos modelos (0,0 em todos os casos), o parâmetro `think: false` e o esquema YAML dos "prompts" de sistema. As variáveis não controladas compreenderam as diferenças arquiteturais entre os sete modelos avaliados e possíveis variações de latência introduzidas pelo servidor Ollama — reconhecidas como limitação do estudo.
