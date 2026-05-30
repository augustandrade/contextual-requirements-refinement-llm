A proposta deste trabalho consiste no desenvolvimento de um sistema baseado em agentes e Large Language Models (LLMs) para apoio à Engenharia de Requisitos, com foco no refinamento semântico e estrutural de requisitos textuais escritos em linguagem natural.

O problema central da pesquisa está relacionado às dificuldades inerentes à documentação textual de requisitos, especialmente ambiguidades linguísticas, requisitos não atômicos, mistura de concerns (functional requirements, quality requirements e constraints) e dependência excessiva de contexto implícito compartilhado entre stakeholders. Tais problemas são amplamente discutidos na literatura clássica de Engenharia de Requisitos, especialmente em Pohl, que aborda textual requirements, ambiguidades em linguagem natural, padrões sintáticos para documentação e critérios de qualidade de requisitos.  

A pesquisa parte do pressuposto de que requisitos frequentemente são produzidos em texto livre, contendo ambiguidades sintáticas, semânticas, lexicais, referenciais e pragmáticas, além de informações implícitas dependentes do domínio de aplicação. Embora o contexto exerça papel fundamental na interpretação correta dos requisitos, a proposta do trabalho não é aumentar a dependência contextual dos artefatos produzidos, mas justamente utilizar contexto controlado como mecanismo de explicitação semântica durante o refinamento, produzindo requisitos mais claros, explícitos e menos dependentes de conhecimento implícito compartilhado.

O sistema receberá como entrada:

* um requisito textual não estruturado escrito em linguagem natural;
* um pequeno contexto controlado contendo informações relevantes de domínio.

O contexto controlado poderá incluir:

* definições terminológicas;
* informações sobre domínio;
* restrições operacionais;
* significados específicos de termos ambíguos;
* informações relevantes para interpretação contextual do requisito.

O trabalho não utiliza mecanismos de retrieval dinâmico de conhecimento externo, bases documentais extensas ou pipelines centrados em Retrieval-Augmented Generation (RAG). O foco da pesquisa está no refinamento semântico e estrutural de requisitos textuais contextualizados.

O processamento será estruturado como um pipeline de refinamento fundamentado na literatura clássica de Engenharia de Requisitos, especialmente em Pohl, contendo as seguintes etapas:

1. Ambiguity Detection
   Identificação de ambiguidades presentes no requisito textual.

2. Ambiguity Classification
   Classificação das ambiguidades identificadas, incluindo ambiguidades sintáticas, semânticas, lexicais, referenciais e pragmáticas.

3. Contextual Resolvability Validation
   Validação de resolubilidade contextual, identificando se a ambiguidade é resolvable, partially_resolvable, blocking ou not_applicable com base apenas no requisito e no contexto disponível.

4. Final Requirement Structuring
   Estruturação final do requisito, incluindo refinamento textual, organização sintática e, quando necessário, operações auxiliares de concern separation e decomposition dentro do próprio processo de structuring.

A proposta não pretende eliminar completamente ambiguidades inerentes à linguagem natural nem substituir atividades humanas de elicitação conduzidas por engenheiros de requisitos. O objetivo do sistema é apoiar atividades de documentação e refinamento textual, identificando problemas linguísticos, sugerindo reformulações e explicitando limitações semânticas quando a resolução automática não for possível.

A saída do sistema será composta por:

* requisitos estruturados;
* classificação dos requirement types;
* ambiguidades identificadas;
* classificação das ambiguidades;
* sugestões de refinamento textual;
* observações sobre concern separation e decomposition quando aplicadas como parte da estruturação final;
* observações sobre ambiguidades não resolvidas automaticamente.

O formato principal de saída do trabalho será documentação textual em linguagem natural estruturada, seguindo princípios sintáticos e critérios de qualidade descritos na literatura clássica de Engenharia de Requisitos.

Do ponto de vista conceitual, o trabalho se posiciona principalmente na dimensão de documentação de requisitos, mantendo relações secundárias com validação e gerenciamento de requisitos. Embora o foco central esteja na documentação estruturada, o trabalho reconhece que atividades de Engenharia de Requisitos são intrinsicamente interdependentes, especialmente no que se refere à relação entre contexto, clareza textual, validação semântica e qualidade dos artefatos produzidos.

A pesquisa concentra-se principalmente nas dimensões:

* Subject (domínio do problema);
* Usage (contexto de uso);
* Technical context.

Essas dimensões são consideradas relevantes por influenciarem diretamente a interpretação semântica e pragmática dos requisitos em linguagem natural.

A avaliação do sistema será qualitativa e fundamentada em literatura, utilizando um corpus controlado de requisitos ambíguos e contextualizados. A análise considerará critérios como:

* identificação correta de ambiguidades;
* classificação adequada dos tipos de ambiguidade;
* separação correta de concerns;
* decomposição adequada de requisitos não atômicos;
* aplicação correta dos templates sintáticos;
* qualidade dos refinamentos sugeridos;
* clareza e explicitação semântica dos requisitos estruturados.

A avaliação utilizará um conjunto previamente analisado manualmente como referência qualitativa para comparação dos resultados produzidos pelo sistema.

Do ponto de vista acadêmico, o trabalho se posiciona como uma pesquisa aplicada em Engenharia de Requisitos, conectando:

* textual requirements;
* ambiguidades em linguagem natural;
* contexto e domínio;
* NLP;
* LLMs;
* sistemas baseados em agentes;
* refinement-oriented requirements engineering.

A contribuição esperada da pesquisa está na investigação de como LLMs e pipelines baseados em agentes podem apoiar o refinamento contextualizado e a estruturação semântica de requisitos textuais, contribuindo para melhoria da clareza, organização e qualidade de artefatos de requisitos produzidos em linguagem natural.
