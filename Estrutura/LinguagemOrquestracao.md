## Estratégia de implementação e orquestração dos agentes

O sistema será implementado em Python como um pipeline orquestrado com agentes funcionais baseados em LLMs. A decisão por uma orquestração própria, em vez de uma plataforma gerenciada de agentes ou de frameworks especializados de orquestração, busca manter o protótipo simples, rastreável e adequado ao escopo experimental do TCC. O objetivo da pesquisa não é avaliar um framework de agentes, mas investigar o uso de LLMs no refinamento semântico e estrutural de requisitos textuais.

O pipeline será reduzido para quatro agentes principais:

1. ambiguity_detector;
2. contextual_resolubility_validator;
3. requirement_structurer;
4. output_consolidator.

O agente requirement_structurer pode executar, quando necessário, operações auxiliares de concern separation e decomposition como parte da estruturação final. Essas operações não são etapas independentes do pipeline; elas só entram em cena quando o requisito mistura funcionalidade, qualidade, restrição ou múltiplas ações independentes, e apenas para produzir uma saída estruturada mais adequada.

Os agentes serão executados sequencialmente, recebendo como entrada o estado produzido pela etapa anterior e gerando uma saída intermediária estruturada. Todas as entradas, saídas intermediárias, prompts e respostas finais serão registradas em arquivos, garantindo rastreabilidade e permitindo análise posterior.

A arquitetura utilizará uma camada abstrata de provedor de LLM, permitindo executar o mesmo pipeline com diferentes modelos. Inicialmente, o desenvolvimento e os testes-piloto serão realizados localmente, utilizando Ollama em um MacBook Pro com Apple Silicon. A implementação será preparada para troca futura do provedor, por exemplo para OpenAI, Azure OpenAI ou Azure AI Foundry, caso os modelos locais não apresentem qualidade suficiente.

Para fins de controle metodológico, a execução oficial do TCC deverá ser realizada com um único modelo principal, com parâmetros fixos, como temperatura, limite de tokens e versão do modelo. Essa decisão busca reduzir variações entre execuções e aumentar a reprodutibilidade do experimento. A camada de abstração do LLM será mantida apenas como estratégia técnica de flexibilidade.

O desenvolvimento seguirá uma abordagem incremental. Primeiro, será implementada a estrutura básica do pipeline e dos arquivos de entrada. Em seguida, serão definidos os prompts de cada agente e o schema da saída final. Antes da execução completa das 45 instâncias experimentais, será realizada uma rodada piloto com requisitos representativos das principais categorias do corpus: um caso de mistura de *concerns*, um caso de ambiguidade linguística/contextual e um caso do grupo de controle. Essa etapa permitirá ajustar os prompts, validar o formato das saídas e verificar se o pipeline respeita as condições de contexto C0, C1 e C2.

A execução completa será realizada somente após a validação do piloto. Para cada requisito e condição de contexto, o sistema salvará a entrada utilizada, a saída de cada agente e a saída consolidada final. Esses artefatos serão armazenados no repositório Git do projeto, juntamente com o corpus, os contextos, os prompts, os logs e os resultados completos, funcionando como material complementar de rastreabilidade e reprodutibilidade.

Frameworks como LangGraph poderão ser considerados em trabalhos futuros, especialmente em cenários que exijam execução durável, ramificações complexas, persistência de estado, integração com ferramentas externas ou intervenção humana no fluxo. Dessa forma, sua não utilização nesta etapa não representa uma limitação conceitual da abordagem, mas uma decisão metodológica voltada à simplicidade, controle experimental e coerência com o escopo do TCC.
