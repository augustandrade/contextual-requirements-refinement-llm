# Perguntas de pesquisa

<!-- Posicionamento: parágrafo(s) de encerramento da Introdução, antes do parágrafo de estrutura do trabalho. Sem subtítulo próprio — incorporar ao fluxo da Introdução. -->

Este estudo investiga em que medida um pipeline multi-agente baseado em modelos de linguagem é capaz de detectar ambiguidades em requisitos de software, avaliar sua resolubilidade em função do contexto disponível e produzir um output estruturado coerente com essa avaliação. O experimento é estruturado em torno de três perguntas de pesquisa, respondidas por meio de avaliação quantitativa automatizada sobre um corpus controlado de 15 requisitos executados sob quatro condições de contexto e sete modelos de linguagem.

**RQ1 — O nível de contexto injetado altera a rota de resolução do pipeline?** Examina se o contexto progressivamente injetado — de nenhum (C0) a específico-irrelevante (C3) — produz mudança observável na rota escolhida pelo pipeline (`structured` ou `signaling`), com a comparação entre C2 e C3 isolando o efeito da relevância com especificidade constante.

**RQ2 — O pipeline distingue requisitos ambíguos de bem formados sem gerar falsos positivos?** Avalia a precisão do Agente 1 na detecção de ambiguidade, com atenção particular à taxa de falsos positivos sobre o grupo de controle (Cat-05), cujos requisitos foram intencionalmente construídos sem defeitos esperados. O desempenho é expresso em precisão, revocação, F1 e especificidade.

**RQ3 — O desempenho varia entre as categorias de defeito do corpus?** Compara o acerto de detecção e a classificação taxonômica entre as quatro categorias positivas: estrutural (Cat-01), linguística (Cat-02), de domínio (Cat-03) e de vaguidade (Cat-04). Para Cat-02, Cat-03 e Cat-04, o tipo de ambiguidade detectado é confrontado com os tipos aceitos declarados no corpus, permitindo identificar quais classes de defeito são mais difíceis de detectar ou classificar corretamente.
