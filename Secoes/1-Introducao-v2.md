# Introdução

A Engenharia de Requisitos [ER] constitui a fase mais crítica do desenvolvimento de software: defeitos introduzidos nesta etapa são os mais custosos para corrigir e respondem por 40% a 50% de todos os defeitos encontrados em um produto de software (Wiegers; Beatty, 2013; Sommerville, 2016). Na prática industrial, a linguagem natural permanece como a principal forma de representação de requisitos, em razão de sua universalidade e facilidade de comunicação entre as partes interessadas (Pohl, 2025; Sommerville, 2016). Entretanto, a documentação em texto livre é essencialmente suscetível a ambiguidades que conduzem as partes interessadas a interpretações divergentes de forma frequentemente inconsciente (Kamsties et al., 2001).

Historicamente, a mitigação dessas ambiguidades dependeu de inspeções manuais metódicas, modelos formais de especificação e *templates* sintáticos para padronização (Pohl, 2025; Wiegers; Beatty, 2013). O avanço dos Modelos de Linguagem de Grande Escala (LLMs — *Large Language Models*) abre novas possibilidades de automação analítica na área: estudos recentes mostram que LLMs conseguem identificar ambiguidades em requisitos textuais e produzir explicações alinhadas ao julgamento humano especializado (Bashir et al., 2025; Cheng et al., 2025). Quando integrados em pipelines baseados em agentes, esses modelos permitem decompor o refinamento textual em etapas com responsabilidade única, reduzindo a complexidade em cada etapa e contribuindo para maior consistência (Gulli, 2025; Zadenoori et al., 2025).

O contexto fornecido a cada agente, no entanto, determina a qualidade da interpretação: sua ausência compromete a leitura semântica do requisito, e o excesso pode introduzir viés e mascarar ambiguidades genuínas (Pohl, 2025; Bashir et al., 2025). Esta pesquisa examina como diferentes níveis e tipos de contexto controlado — de nenhum a genérico, específico-relevante e específico-irrelevante — afetam a capacidade do pipeline de detectar e resolver ambiguidades.

O presente trabalho desenvolveu e avaliou um pipeline multi-agente de LLMs capaz de detectar ambiguidades em requisitos escritos em linguagem natural e de resolvê-las com base no contexto disponível. O sistema foi executado sobre um corpus controlado de 15 requisitos em quatro condições de contexto, totalizando 60 instâncias experimentais, cada uma executada nos sete modelos de linguagem de código aberto — 420 execuções no total.

O experimento é estruturado em torno de três perguntas de pesquisa:

**RQ1 — O nível de contexto injetado altera a rota de resolução do pipeline?** Examina se o contexto progressivamente injetado — de nenhum (C0) a específico-irrelevante (C3) — produz mudança observável na rota escolhida (`structured` ou `signaling`), com a comparação entre C2 e C3 isolando o efeito da relevância com especificidade constante.

**RQ2 — O pipeline distingue requisitos ambíguos de bem formados sem gerar falsos positivos?** Avalia a precisão do Agente 1 na detecção de ambiguidade, com atenção particular à taxa de falsos positivos sobre o grupo de controle (Cat-05). O desempenho é expresso em precisão, revocação, F1 e especificidade.

**RQ3 — O desempenho varia entre as categorias de defeito do corpus?** Compara o acerto de detecção e a classificação taxonômica entre as quatro categorias positivas — estrutural, linguística, de domínio e de vaguidade —, identificando quais classes de defeito são mais difíceis de detectar ou classificar corretamente.

## Objetivos específicos

Os objetivos específicos são:

- Projetar e implementar o **Agente 1** (Detector de Ambiguidades), responsável pela identificação e classificação de ambiguidades linguísticas segundo a taxonomia de Pohl (2025), operando sem acesso a qualquer informação contextual;
- Projetar e implementar o **Agente 2** (Verificação de Resolubilidade), responsável por avaliar, com base no contexto controlado fornecido, se cada ambiguidade identificada pelo Agente 1 é resolúvel;
- Projetar e implementar o **Agente 3** (Estruturador), responsável pela produção do requisito estruturado nos casos em que o status global for `fully_resolvable` ou `no_ambiguity`;
- Construir um corpus controlado de 15 requisitos em linguagem natural, distribuídos em cinco categorias de defeitos textuais e quatro condições de contexto (C0–C3);
- Implementar um consolidador determinístico em Python para orquestrar a execução dos agentes e produzir outputs padronizados;
- Avaliar o desempenho do pipeline por meio de quatro blocos de métricas quantitativas, calculadas automaticamente contra uma referência manual embutida no corpus; e
- Avaliar qualitativamente os outputs do Agente 3 por meio de checklist baseado nos critérios de qualidade de Pohl (2025).
