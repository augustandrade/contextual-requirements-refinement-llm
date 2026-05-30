# Material e Métodos

A pesquisa caracterizou-se como um estudo de natureza aplicada, exploratória e descritiva, com abordagem qualitativa e procedimento experimental computacional. O caráter aplicado justificou-se pela investigação de uma solução computacional voltada a um problema prático da Engenharia de Requisitos: o refinamento semântico e estrutural de requisitos textuais escritos em linguagem natural. O viés exploratório relacionou-se à investigação do uso de Modelos de Linguagem de Grande Escala, do inglês Large Language Models (LLMs), no refinamento textual, abordagem de automação ainda emergente no contexto da Engenharia de Requisitos. O caráter descritivo, por sua vez, permitiu detalhar o comportamento do sistema durante a reestruturação dos textos analisados.

A abordagem qualitativa foi adotada porque a avaliação do sistema não se concentrou na mensuração estatística de desempenho, mas na análise interpretativa da adequação das saídas produzidas pelo protótipo em relação a critérios derivados da literatura de Engenharia de Requisitos. Dessa forma, buscou-se compreender como o sistema identificou ambiguidades, utilizou informações contextuais e estruturou requisitos textuais em linguagem natural.

## Objeto de análise e materiais utilizados

O objeto de análise deste estudo constituiu-se de requisitos textuais escritos em linguagem natural, selecionados da literatura de Engenharia de Requisitos e de estudos recentes sobre ambiguidades em requisitos. Os requisitos foram escolhidos por apresentarem problemas previamente conhecidos, como ambiguidades, não atomicidade, mistura de concerns, termos vagos, lacunas de informação contextual ou, no caso do grupo de controle, ausência de problemas estruturais relevantes esperados.

Os requisitos foram mantidos no idioma original das fontes, majoritariamente em inglês, com o objetivo de preservar as ambiguidades linguísticas, sintáticas, referenciais, semânticas e pragmáticas presentes nos textos originais. Essa decisão também se justificou pelo fato de que o idioma de execução constitui uma variável relevante em experimentos com LLMs. Estudos recentes indicam que modelos multilíngues podem apresentar forte influência do inglês tanto em seus espaços representacionais quanto na naturalidade lexical e sintática de suas saídas em outros idiomas (SCHUT; GAL; FARQUHAR, 2025; GUO et al., 2025). Além disso, avaliações em português demandam atenção específica às particularidades linguísticas, culturais e regionais da língua, uma vez que tarefas traduzidas podem não capturar adequadamente nuances próprias do português brasileiro (ALMEIDA et al., 2025). Assim, a tradução dos requisitos poderia alterar o fenômeno linguístico analisado, criando ou removendo ambiguidades relevantes para o estudo. Por esse motivo, embora o trabalho tenha sido redigido em português, o corpus, os contextos controlados e as saídas experimentais do sistema foram mantidos em inglês.


Para a condução do estudo, foram utilizados os seguintes materiais:

* um corpus controlado composto por 15 requisitos textuais;
* três condições de contexto para cada requisito: C0, C1 e C2;
* literatura de referência em Engenharia de Requisitos para embasar a análise de ambiguidades, a separação por tipo de requisito, a decomposição de requisitos não atômicos e os padrões sintáticos utilizados;
* um protótipo computacional implementado em Python;
* Modelos de Linguagem de Grande Escala integrados a um pipeline orquestrado com agentes funcionais;
* prompts específicos para cada agente funcional;
* registros intermediários, logs e saídas finais gerados durante a execução do sistema;
* referência manual de análise para apoiar a avaliação qualitativa das saídas;
* checklist de avaliação qualitativa.

## Corpus controlado

O corpus controlado foi organizado em quatro categorias de análise:

1. problemas estruturais e mistura de concerns;
2. ambiguidades linguísticas e sintáticas;
3. ambiguidades específicas de domínio ou contexto;
4. grupo de controle.

A primeira categoria reuniu requisitos com problemas de estruturação textual, como requisitos não atômicos, múltiplas ações em uma mesma sentença, mistura entre funcionalidade, atributo de qualidade e restrição, ou formulações em voz passiva que ocultavam atores relevantes.

A segunda categoria reuniu requisitos cuja dificuldade principal estava na própria estrutura da linguagem natural, como pronomes vagos, construções sintáticas ambíguas, conectivos lógicos com precedência incerta e termos fracos ou pouco verificáveis.

A terceira categoria reuniu requisitos cuja interpretação dependia fortemente de informações específicas de domínio, regras operacionais ou restrições técnicas. Esses casos foram especialmente relevantes para avaliar a etapa de validação de resolubilidade contextual.

A quarta categoria reuniu requisitos sem problemas estruturais relevantes esperados. O objetivo desse grupo foi verificar se o sistema preservava requisitos já adequadamente estruturados, evitando alterações desnecessárias ou degradação da especificação.

A versão consolidada do corpus foi composta por 15 textos-base. Cada texto-base foi submetido a três condições de contexto, totalizando 45 execuções experimentais:

```text
15 textos-base × 3 condições de contexto = 45 execuções experimentais
```

A distinção entre texto-base e instância experimental foi adotada para evitar ambiguidade metodológica. O texto-base corresponde ao requisito selecionado da literatura. A instância experimental corresponde à combinação entre esse requisito e uma condição específica de contexto.

## Contexto controlado

O contexto controlado foi definido como uma estrutura textual padronizada utilizada para fornecer ao sistema informações adicionais sobre o domínio, os termos, as regras de negócio e as restrições associadas a cada requisito. Como diferentes tipos de ambiguidades e problemas textuais exigem diferentes recortes de conhecimento para serem analisados, o contexto foi organizado em blocos explícitos, permitindo controlar o grau de informação fornecido ao modelo.

A estruturação do contexto foi relevante porque a interpretação de requisitos escritos em linguagem natural pode depender de informações que não estão presentes no próprio requisito, mas que fazem parte do domínio, do ambiente operacional ou das convenções compartilhadas entre os envolvidos. Assim, o contexto controlado foi utilizado como mecanismo de explicitação semântica, permitindo avaliar em que medida diferentes níveis de informação contextual influenciaram a identificação, a resolubilidade e o refinamento dos requisitos textuais.

Nos casos em que houve injeção de contexto, foi adotada uma estrutura em XML/Markdown composta por quatro blocos:

```xml
<controlled_context>
  <domain>
    Brief description of the system domain, operational environment, actors, and business process.
  </domain>

  <glossary>
    - "Term": Domain-specific definition.
  </glossary>

  <business_rules>
    - BR-01: Business rule relevant to the interpretation of the requirement.
  </business_rules>

  <constraints>
    - Constraint relevant to the system, process, technology, law, or quality attribute.
  </constraints>
</controlled_context>
```

O bloco `domain` foi utilizado para indicar o domínio, o ambiente operacional, os atores e o escopo do sistema. O bloco `glossary` foi utilizado para definir termos, siglas, jargões e entidades relevantes. O bloco `business_rules` registrou regras de negócio, políticas, critérios de decisão ou condições operacionais. O bloco `constraints` registrou restrições técnicas, legais, organizacionais, operacionais ou de qualidade.

## Condições experimentais de contexto

Para reduzir o viés de fornecer ao modelo apenas um contexto diretamente resolutivo, o delineamento experimental considerou três níveis de contexto: C0, C1 e C2.

Na condição C0 — sem contexto, o requisito textual foi submetido ao sistema sem bloco contextual adicional. Operacionalmente, essa condição correspondeu à execução sem envio do bloco `<controlled_context>` ao modelo. Essa condição funcionou como linha de base, permitindo observar o que o sistema conseguia identificar apenas a partir da estrutura linguística do requisito e do conhecimento geral do modelo. Esperou-se que, nessa condição, o sistema fosse capaz de detectar ambiguidades e problemas textuais, mas evitasse resolver ambiguidades dependentes de informações específicas de domínio.

Na condição C1 — contexto geral, o requisito foi acompanhado de um contexto amplo, contendo informações sobre domínio, atores, ambiente operacional ou finalidade do sistema, mas sem incluir explicitamente a regra, definição ou restrição necessária para resolver a ambiguidade principal. Essa condição permitiu verificar se um contexto geral já seria suficiente para melhorar a interpretação e a estruturação do requisito ou se a ambiguidade permaneceria bloqueante. O objetivo foi observar se o sistema utilizava o contexto de forma conservadora, sem introduzir inferências não sustentadas.

Na condição C2 — contexto resolutivo, o requisito foi acompanhado de um contexto contendo definições, regras de negócio ou restrições suficientes para orientar uma interpretação específica. Essa condição permitiu avaliar se, quando a evidência contextual estava explicitamente disponível, o sistema conseguia utilizá-la adequadamente para reduzir ambiguidades e produzir uma estruturação textual mais clara e semanticamente explícita. Operações de concern separation e decomposition passaram a ocorrer dentro da etapa de estruturação final, e não como fases independentes.

## Procedimento de desenvolvimento do sistema

O sistema foi desenvolvido como um pipeline orquestrado com agentes funcionais baseados em LLMs. A decisão por uma orquestração própria, em vez de uma plataforma gerenciada de agentes ou de frameworks especializados de orquestração, buscou manter o protótipo simples, rastreável e adequado ao escopo experimental do trabalho. Como o objetivo da pesquisa não foi avaliar uma plataforma ou framework específico de agentes, mas investigar o uso de LLMs no refinamento semântico e estrutural de requisitos textuais, a implementação foi organizada de forma modular e independente de provedor.

O protótipo foi implementado em Python. Cada agente funcional foi responsável por uma etapa específica do pipeline, recebendo como entrada o estado produzido pela etapa anterior e gerando uma saída intermediária estruturada. Todas as entradas, saídas intermediárias, prompts e respostas finais foram registradas em arquivos, garantindo rastreabilidade e permitindo análise posterior.

Embora frameworks como LangChain e LangGraph ofereçam recursos robustos para construção e orquestração de agentes, optou-se inicialmente por uma orquestração própria em Python. Essa decisão justificou-se pelo caráter controlado e sequencial do experimento, no qual cada agente funcional executou uma etapa previamente definida do pipeline. Como o fluxo proposto foi determinístico e composto por etapas conhecidas, a adoção desses frameworks poderia introduzir abstrações e dependências externas desnecessárias para o objetivo da pesquisa. Além disso, uma implementação modular própria permitiu maior controle sobre entradas, prompts, saídas intermediárias, arquivos de log e resultados finais, facilitando a rastreabilidade metodológica.

A arquitetura utilizou uma camada abstrata de provedor de LLM, permitindo executar o mesmo pipeline com diferentes modelos. Inicialmente, o desenvolvimento e os testes-piloto foram planejados para execução local com Ollama em ambiente Apple Silicon. A implementação, entretanto, foi preparada para permitir troca futura do provedor, por exemplo para OpenAI, Azure OpenAI ou Azure AI Foundry, caso os modelos locais não apresentassem qualidade suficiente para a execução experimental.

Para fins de controle metodológico, a execução experimental oficial foi planejada com um único modelo principal, com parâmetros fixos, como temperatura, limite de tokens e versão do modelo. Essa decisão buscou reduzir variações entre execuções e aumentar a reprodutibilidade do experimento. A camada de abstração do LLM foi mantida apenas como estratégia técnica para flexibilidade, não como variável central da pesquisa.

## Arquitetura do pipeline de agentes

A arquitetura foi organizada em quatro agentes funcionais executados sequencialmente:

1. ambiguity_detector;
2. contextual_resolubility_validator;
3. requirement_structurer;
4. output_consolidator.

O ambiguity_detector teve como função identificar trechos ambíguos ou problemáticos no requisito original, classificando-os em categorias como ambiguidade lexical, sintática, semântica, referencial, lógica ou pragmático-contextual. Esse agente não teve como responsabilidade resolver ambiguidades, mas apenas identificá-las, descrevê-las e listar interpretações possíveis.

O contextual_resolubility_validator avaliou se as ambiguidades identificadas poderiam ser resolvidas com base no requisito original e no contexto disponível. Para cada ambiguidade, esse agente classificou a situação como resolvable, partially_resolvable, blocking ou not_applicable. A ambiguidade só foi considerada resolvable quando havia evidência suficiente no requisito ou no contexto fornecido. Quando a evidência era insuficiente, a ambiguidade deveria ser sinalizada como blocking ou partially_resolvable.

O requirement_structurer produziu a estrutura final do requisito. Esse agente pode executar, quando necessário, operações auxiliares de concern separation e decomposition como parte da estruturação final. Essas operações não foram tratadas como etapas independentes; elas só foram acionadas quando o requisito misturava funcionalidade, qualidade, restrição ou múltiplas ações independentes. O agente poderia explicitar termos definidos no contexto, substituir termos vagos por termos mais precisos, remover voz passiva quando o ator fosse conhecido e substituir modalidade fraca quando o contexto sustentasse essa alteração. Entretanto, não deveria inventar atores, prazos, regras de negócio ou resolver ambiguidades classificadas como blocking.

O output_consolidator reuniu as saídas intermediárias dos agentes anteriores em um único resultado final estruturado, contendo análise de ambiguidades, análise de resolubilidade contextual, estruturação final do requisito, ambiguidades não resolvidas e observações finais.

O fluxo decisório do pipeline foi definido da seguinte forma: ambiguidades resolúveis seguiram para refinamento e estruturação; ambiguidades parcialmente resolúveis permitiram refinamento das partes sustentadas e sinalização das pendências; ambiguidades bloqueantes não foram resolvidas automaticamente, sendo registradas com justificativa, informação ausente e, quando aplicável, pergunta de esclarecimento; requisitos sem problemas relevantes foram preservados ou receberam apenas ajustes formais mínimos.

## Formato de saída do sistema

O formato de saída do sistema foi definido como uma estrutura própria inspirada nas diretrizes de Pohl, combinando separação por tipo de requisito e padronização sintática para os requisitos que pudessem ser estruturados de forma controlada.

Dessa forma, o sistema não produziu apenas uma reformulação textual livre, mas uma representação estruturada contendo metadados do requisito, como identificador, tipo, condição, sistema ou componente responsável, ator envolvido quando aplicável, obrigatoriedade, ação, objeto e sentença final refinada. Para requisitos de qualidade e restrições, a saída preservou estruturas próprias, relacionando-as ao requisito funcional correspondente quando houve dependência semântica. Quando necessário, concern separation e decomposition foram aplicadas dentro da etapa de estruturação final.

Essa decisão metodológica buscou tornar explícitas as informações utilizadas na reestruturação textual sem transformar separação de concerns e decomposição em etapas independentes do pipeline.

## Referência manual de análise

Para apoiar a avaliação qualitativa dos resultados, foi elaborada uma referência manual de análise para cada requisito do corpus controlado. Essa referência não teve como objetivo estabelecer uma resposta textual única ou uma formulação exata esperada para cada requisito, uma vez que diferentes reformulações podem ser consideradas adequadas desde que preservem o sentido do requisito e atendam aos critérios de qualidade definidos na pesquisa.

A referência manual foi utilizada como instrumento de orientação para a aplicação do checklist de avaliação. Para cada requisito e para cada condição de contexto — C0, C1 e C2 — foram registrados o grau esperado de resolubilidade, as ações esperadas do sistema, os problemas que deveriam ser identificados, os comportamentos que deveriam ser evitados e os critérios de avaliação aplicáveis.

O grau esperado de resolubilidade foi classificado em quatro possibilidades: resolvable, quando havia informação suficiente para refinar ou estruturar o requisito; partially_resolvable, quando parte do requisito poderia ser refinada, mas ainda permanecia alguma lacuna relevante; blocking, quando a ambiguidade ou problema textual não poderia ser resolvido com a informação disponível; e not_applicable, utilizado principalmente nos casos de controle, quando não havia ambiguidade ou problema textual relevante esperado.

Dessa forma, a referência manual funcionou como uma base analítica intermediária entre o corpus e a avaliação final. Ela permitiu que a análise das saídas não dependesse de comparação literal com uma sentença esperada, mas sim da verificação qualitativa da adequação do comportamento do sistema em relação aos problemas previamente definidos para cada requisito.

## Procedimento de aplicação e coleta de dados

O procedimento de aplicação consistiu na execução do protótipo sobre o corpus controlado. Cada requisito foi submetido ao sistema em três condições de contexto: C0, C1 e C2. Assim, foram realizadas 45 execuções experimentais.

Antes da execução completa, foi prevista uma rodada piloto com requisitos representativos das principais categorias do corpus: um caso de mistura de concerns, um caso de ambiguidade linguística ou contextual e um caso do grupo de controle. Essa etapa teve como objetivo ajustar os prompts, validar o formato das saídas e verificar se o pipeline respeitava as condições de contexto definidas.

A execução completa foi planejada somente após a validação do piloto. Para cada requisito e condição de contexto, o sistema registrou a entrada utilizada, o contexto injetado quando aplicável, a saída de cada agente funcional e a saída consolidada final.

A coleta de dados ocorreu durante a execução do pipeline. Foram extraídos e armazenados três conjuntos principais de informações:

* as entradas fornecidas ao sistema, compostas pelo requisito original e pelo contexto quando aplicável;
* os registros intermediários, contendo explicações textuais, classificações atribuídas, interpretações possíveis, decisões de resolubilidade e justificativas sintéticas produzidas pelos agentes;
* as saídas finais, compostas pelos requisitos refinados, estruturados sintaticamente e consolidados, bem como pelas ambiguidades bloqueantes sinalizadas.

Para fins de transparência e reprodutibilidade, os artefatos produzidos durante a pesquisa, incluindo corpus, contextos controlados, referência manual de análise, prompts, registros intermediários, saídas completas, logs e scripts de execução, foram organizados em um repositório Git. No corpo do trabalho, foram apresentados apenas os resultados mais relevantes para a análise e discussão, em formato de tabelas e exemplos selecionados.

## Checklist de avaliação qualitativa

A avaliação qualitativa das saídas foi realizada por meio de um checklist analítico composto por seis critérios: ambiguidade, resolubilidade contextual, clareza textual, estruturação sintática, explicitação semântica e estruturação final do requisito. A seleção desses critérios foi fundamentada na literatura de Engenharia de Requisitos e em estudos recentes sobre LLMs aplicados à área.

O critério de ambiguidade apoia-se na discussão sobre múltiplas interpretações em linguagem natural. A resolubilidade contextual deriva da dependência de conhecimento de domínio e contexto para interpretar requisitos. A clareza textual associa-se à precisão, compreensibilidade e verificabilidade. A estruturação sintática fundamenta-se no uso de padrões de sentença e linguagem natural controlada. A explicitação semântica com controle de inferência considera a necessidade de ancorar as saídas em informações fornecidas, evitando inferências não sustentadas. A estruturação final do requisito incorpora, quando necessário, concern separation e decomposition como operações auxiliares.

Cada critério foi avaliado por meio de uma escala qualitativa simples: adequado, parcialmente adequado, inadequado ou não aplicável. A avaliação não buscou verificar correspondência literal com uma resposta esperada, mas analisar se a saída do sistema se comportou de maneira compatível com a referência manual de análise e com o checklist definido. Para cada julgamento, foi registrada uma justificativa textual curta, permitindo rastreabilidade da avaliação.

## Análise dos dados

A análise dos dados baseou-se na avaliação qualitativa das saídas geradas pelo protótipo. A adequação do refinamento foi interpretada a partir da comparação entre o requisito textual original, a condição de contexto utilizada, a referência manual de análise e a saída produzida pelo sistema.

A análise buscou verificar se o sistema foi capaz de:

* identificar ambiguidades e problemas textuais esperados;
* distinguir ambiguidades resolúveis, parcialmente resolúveis e bloqueantes;
* utilizar informações contextuais de forma adequada;
* evitar inferências não sustentadas pelo requisito ou pelo contexto;
* estruturar requisitos que misturam funcionalidade, qualidade, restrição ou múltiplas ações independentes;
* aplicar concern separation e decomposition apenas como operações auxiliares dentro da estruturação final;
* preservar requisitos do grupo de controle;
* produzir requisitos refinados e estruturados de forma clara e semanticamente explícita.

Os resultados foram organizados em tabelas sintéticas e exemplos selecionados. A análise comparou o comportamento do sistema entre as condições C0, C1 e C2, permitindo observar em que medida a ausência de contexto, o contexto geral e o contexto resolutivo influenciaram a identificação, a sinalização ou a resolução de ambiguidades.

No corpo do trabalho, foram discutidos apenas os casos mais relevantes para a análise, incluindo exemplos de resolução adequada, ambiguidades bloqueantes, refinamento parcial, preservação de requisitos de controle e ao menos um caso de resultado parcialmente adequado ou inadequado. Os resultados completos foram mantidos no repositório Git como material complementar.

Como delimitação metodológica, os resultados deste estudo restringem-se a requisitos textuais analisados em inglês. Embora o problema da ambiguidade em linguagem natural não seja exclusivo desse idioma, a generalização dos resultados para requisitos em português exige nova avaliação com corpus originalmente produzido em português, de modo a preservar fenômenos linguísticos, culturais e regionais próprios da língua.

