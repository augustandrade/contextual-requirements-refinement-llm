# Introdução

A Engenharia de Requisitos [ER] constitui a fase mais crítica do desenvolvimento de software, pois os defeitos introduzidos nesta etapa são os mais custosos para corrigir (Sommerville, 2016; Wiegers e Beatty, 2013). Estudos indicam que erros introduzidos durante as atividades de requisitos respondem por 40% a 50% de todos os defeitos encontrados em um produto de software (Wiegers; Beatty, 2013), estimativa amplamente referenciada na literatura ainda que a conexão empírica entre qualidade de requisitos e defeitos subsequentes permaneça pouco explorada por estudos recentes (Femmer et al., 2023), reflexo direto das dificuldades inerentes à forma como os requisitos são comunicados.

Na prática industrial, a linguagem natural permanece como a principal forma de representação de requisitos, em razão de sua universalidade, expressividade e facilidade de comunicação entre as diversas partes interessadas (Pohl, 2025; Kamsties et al., 2001; Sommerville, 2016). Entretanto, a documentação em texto livre traz limitações próprias, uma vez que a linguagem natural é essencialmente suscetível a ambiguidades que conduzem as partes interessadas a interpretações divergentes de forma frequentemente inconsciente (Kamsties et al., 2001).

Pohl (2025) classifica as ambiguidades em requisitos em cinco categorias: lexical, sintática, semântica, referencial e vaguidade. Cada tipo compromete a qualidade da especificação de formas distintas: ambiguidades lexicais introduzem polissemia em termos técnicos; as sintáticas geram árvores de análise alternativas; as semânticas decorrem de operadores lógicos indefinidos; as referenciais surgem de anáforas com múltiplos antecedentes; e a vaguidade impede a verificação objetiva de critérios.

Historicamente, a mitigação dessas ambiguidades textuais dependeu de inspeções manuais metódicas, modelos formais de especificação, tais como extensões do WRSPM para requisitos em linhas de produto (Virissimo, 2014), e da utilização de *templates* sintáticos para padronização (Pohl, 2025; Wiegers; Beatty, 2013). O avanço do Processamento de Linguagem Natural [PLN] e o desenvolvimento dos Modelos de Linguagem de Grande Escala (LLMs — *Large Language Models*) abrem novas possibilidades de automação analítica para a área de Engenharia de Requisitos (Cheng et al., 2025).

O uso de LLMs, impulsionado por estratégias como o aprendizado em contexto (*in-context learning*), tem apresentado resultados promissores na identificação de ambiguidades em requisitos textuais, inclusive com capacidade de produzir explicações alinhadas ao julgamento humano especializado (Bashir et al., 2025). Quando integrados em pipelines baseados em agentes, esses modelos permitem decompor o refinamento textual em etapas com responsabilidade única (Gulli, 2025), reduzindo a complexidade em cada etapa e contribuindo para maior consistência (Zadenoori et al., 2025).

O contexto fornecido a cada agente, no entanto, determina a qualidade da interpretação: sua ausência compromete a leitura semântica do requisito, e o excesso pode introduzir viés e mascarar ambiguidades genuínas (Pohl, 2025; Bashir et al., 2025). O contexto controlado — definições, terminologias de domínio e restrições — atua como mecanismo de explicitação semântica durante o refinamento textual (Pohl, 2025). Esta pesquisa examina como diferentes níveis e tipos de contexto controlado afetam essa capacidade de resolução.

O presente trabalho desenvolveu e avaliou um pipeline multi-agente de LLMs capaz de detectar ambiguidades em requisitos escritos em linguagem natural e de resolvê-las com base no contexto disponível. O sistema foi executado sobre um corpus controlado de 15 requisitos em quatro condições de contexto (C0, C1, C2 e C3), totalizando 60 instâncias experimentais, cada uma executada nos sete modelos de linguagem de código aberto — 420 execuções no total.

O experimento é estruturado em torno de três perguntas de pesquisa, respondidas por meio de avaliação quantitativa automatizada:

**RQ1 — O nível de contexto injetado altera a rota de resolução do pipeline?** Examina se o contexto progressivamente injetado — de nenhum (C0) a específico-irrelevante (C3) — produz mudança observável na rota escolhida pelo pipeline (`structured` ou `signaling`), com a comparação entre C2 e C3 isolando o efeito da relevância com especificidade constante.

**RQ2 — O pipeline distingue requisitos ambíguos de bem formados sem gerar falsos positivos?** Avalia a precisão do Agente 1 na detecção de ambiguidade, com atenção particular à taxa de falsos positivos sobre o grupo de controle (Cat-05), cujos requisitos foram intencionalmente construídos sem defeitos esperados. O desempenho é expresso em precisão, revocação, F1 e especificidade.

**RQ3 — O desempenho varia entre as categorias de defeito do corpus?** Compara o acerto de detecção e a classificação taxonômica entre as quatro categorias positivas: estrutural (Cat-01), linguística (Cat-02), de domínio (Cat-03) e de vaguidade (Cat-04). Para Cat-02, Cat-03 e Cat-04, o tipo de ambiguidade detectado é confrontado com os tipos aceitos declarados no corpus, permitindo identificar quais classes de defeito são mais difíceis de detectar ou classificar corretamente.

## Objetivos específicos

Os objetivos específicos são:

- Projetar e implementar o **Agente 1** (Detector de Ambiguidades), responsável pela identificação e classificação de ambiguidades linguísticas segundo a taxonomia de Pohl (2025) — lexical, sintática, semântica, referencial e vaguidade —, operando sem acesso a qualquer informação contextual;
- Projetar e implementar o **Agente 2** (Verificação de Resolubilidade), responsável por avaliar, com base no contexto controlado fornecido, se cada ambiguidade identificada pelo Agente 1 é resolúvel;
- Projetar e implementar o **Agente 3** (Estruturador), responsável pela produção do requisito estruturado nos casos em que o status global for `fully_resolvable` ou `no_ambiguity`;
- Construir um corpus controlado de 15 requisitos em linguagem natural, distribuídos em cinco categorias de defeitos textuais e quatro condições de contexto (C0–C3);
- Implementar um consolidador determinístico em Python para orquestrar a execução dos agentes e produzir outputs padronizados;
- Avaliar o desempenho do pipeline por meio de quatro blocos de métricas quantitativas, calculadas automaticamente contra uma referência manual embutida no corpus; e
- Avaliar qualitativamente os outputs do Agente 3 por meio de checklist baseado nos critérios de qualidade de Pohl (2025).
