Propõe-se sistema baseado em agentes e LLMs para apoio à Engenharia de Requisitos, com foco na identificação, refinamento e estruturação de requisitos textuais escritos em linguagem natural.

O problema central da pesquisa está relacionado às dificuldades inerentes à documentação de requisitos em linguagem natural, especialmente ambiguidades, requisitos não atômicos, mistura de concerns (funcionais, qualidade e constraints) e dependência de contexto implícito entre stakeholders. O trabalho se fundamenta principalmente na segunda edição do livro Requirements Engineering, que discute problemas de textual requirements, ambiguidades e padrões sintáticos para documentação de requisitos.

A proposta considera que requisitos frequentemente são escritos em texto livre, contendo informações vagas, ambiguidades sintáticas, semânticas, lexicais e referenciais. Além disso, assume-se que o contexto de domínio exerce papel fundamental na interpretação correta dos requisitos, embora o objetivo da estruturação seja justamente reduzir a dependência de conhecimento implícito e produzir requisitos mais claros e semanticamente explícitos.

O sistema receberá como entrada:

um requisito textual não estruturado;

um pequeno contexto controlado contendo informações relevantes de domínio.

O processamento seguirá um pipeline fundamentado em Pohl:

análise de ambiguidades;

classificação das ambiguidades identificadas;

identificação de ambiguidades bloqueantes;

sugestão de refinamentos textuais;

separação de concerns (functional requirements, quality requirements e constraints);

decomposição de requisitos não atômicos;

estruturação sintática utilizando o template textual de Pohl.

O sistema não pretende eliminar completamente ambiguidades nem substituir a elicitação conduzida por engenheiros de requisitos. Sua proposta é apoiar o refinamento e a documentação estruturada de requisitos, sugerindo reformulações e explicitando problemas textuais quando possível.

A saída do sistema conterá:

requisitos estruturados;

classificação dos requirement types;

ambiguidades identificadas;

sugestões de refinamento;

observações sobre ambiguidades não resolvidas automaticamente.

A avaliação será qualitativa e baseada em literatura, utilizando um corpus controlado de requisitos ambíguos e contextualizados. Os critérios de avaliação incluirão:

identificação correta de ambiguidades;

identificação do tipo de ambiguidade;

separação adequada de concerns;

decomposição de requisitos não atômicos;

aplicação correta do template sintático;

qualidade dos refinamentos sugeridos.

O trabalho utiliza documentação textual em linguagem natural como formato principal de saída, seguindo os padrões sintáticos e princípios de qualidade de requisitos descritos por Pohl. O foco da pesquisa não está em retrieval, embeddings ou RAG, mas sim no refinamento semântico e estrutural de requisitos textuais contextualizados.

Do ponto de vista acadêmico, o trabalho se posiciona como uma pesquisa aplicada em Engenharia de Requisitos, conectando:

textual requirements;

ambiguidades em linguagem natural;

contexto e domínio;

NLP;

LLMs;

sistemas baseados em agentes;

refinement-oriented requirements engineering.