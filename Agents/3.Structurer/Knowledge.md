Com base na literatura de Engenharia de Requisitos fornecida, apresento a seguir o conhecimento fundamental sobre os tipos de ambiguidades, os mecanismos para resolvê-las e as regras de estruturação textual.

### 1. Conhecimento sobre Ambiguidades

A linguagem natural é universal e expressiva, mas inerentemente suscetível a múltiplas interpretações, o que pode levar desenvolvedores a implementar soluções erradas de forma inconsciente. A literatura classifica as ambiguidades nas seguintes categorias principais:

*   **Ambiguidade Léxica:** Ocorre quando uma palavra ou expressão possui múltiplos significados. Ela é causada por sinônimos (palavras diferentes com o mesmo sentido), homônimos (mesma grafia/pronúncia, mas significados diferentes, como "banco") e polissemia (múltiplos significados relacionados para a mesma palavra).
*   **Ambiguidade Sintática (ou Estrutural):** Acontece quando a estrutura gramatical da frase permite a construção de mais de uma árvore sintática válida. Um exemplo clássico é: *"O usuário insere o cartão de acesso com o código de acesso"*, onde não fica claro se o código está impresso no cartão ou se o usuário digita o código separadamente.
*   **Ambiguidade Semântica (ou Lógica):** Ocorre quando o sentido global da frase permite interpretações lógicas distintas, mesmo sem problemas léxicos ou sintáticos. Ocorre frequentemente quando os operadores lógicos "E" e "OU" são misturados na mesma frase, pois a linguagem natural não possui regras claras de precedência matemática.
*   **Ambiguidade Referencial:** Causada por anáforas ou pronomes (como "ele", "isso", "eles") que podem se referir a múltiplos objetos mencionados anteriormente. Por exemplo, *"O usuário insere o cartão e digita o PIN. Se ele for inválido..."* não deixa claro se "ele" se refere ao cartão ou ao PIN.
*   **Vagueza (Termos Fracos):** Ocorre quando há o uso de palavras subjetivas ou quantificadores universais em que é impossível determinar a fronteira exata do termo. Exemplos incluem adjetivos como "tamanho médio", "rápido" ou "adequado", que dependem de interpretação pessoal.
*   **Ambiguidade Pragmática / de Domínio (Específica de RE):** Ocorre quando o texto parece gramaticalmente correto, mas a sua interpretação depende de conhecimento implícito do domínio de aplicação. Por exemplo, *"desligue as bombas se o nível da água permanecer alto por 4 segundos"* é ambíguo porque exige conhecimento do domínio para saber se o sistema deve considerar a média de 4 segundos, a mediana ou o valor mínimo no período.

### 2. Como Resolver as Ambiguidades

A resolução de ambiguidades foca em tornar as informações implícitas em explícitas e reduzir o espaço de interpretação do leitor:

*   **Uso de Glossários Controlados:** A principal forma de eliminar ambiguidades léxicas e vagueza é definir o significado exato, as unidades de medida e os sinônimos de termos técnicos e de negócio em um glossário compartilhado entre os *stakeholders*.
*   **Explicitação de Contexto e Regras de Negócio:** Para resolver as ambiguidades pragmáticas ou de domínio, é necessário fornecer o contexto controlado. Se uma frase depende de um conhecimento de mundo implícito, esse conhecimento deve ser documentado como uma regra de negócio (ex: definir o que constitui exatamente a regra de "4 segundos" da bomba d'água).
*   **Uso de Voz Ativa e Explicitação de Atores:** Requisitos escritos na voz passiva (ex: *"o alerta será disparado"*) omitem frequentemente quem ou o que realiza a ação. A resolução exige a reescrita na voz ativa para garantir que cada verbo de processo tenha um sujeito explícito.
*   **Substituição de Referências:** A ambiguidade referencial é resolvida eliminando-se o uso de pronomes vagos e repetindo o substantivo exato ao qual a frase se refere.
*   **Decomposição Lógica (Tabelas de Decisão):** Para resolver a ambiguidade semântica de múltiplas condições (o problema do "E/OU"), a frase deve ser decomposta. Se a lógica for muito complexa, deve-se substituir a linguagem livre por árvores ou tabelas de decisão para cobrir todas as combinações lógicas.

### 3. Como Estruturar os Requisitos

Para que o requisito resultante do refinamento seja de alta qualidade e livre de defeitos estruturais, a literatura estabelece diretrizes rigorosas de estruturação:

**A. Atomicidade e Decomposição**
Deve-se formular apenas um único requisito funcional por sentença. Requisitos que possuem mais de uma ação ou resposta do sistema na mesma frase (conectados por "e", por exemplo) devem ser decompostos em unidades menores e independentes para facilitar a testabilidade.

**B. Separação de *Concerns* (Preocupações)**
Muitos problemas estruturais surgem quando dados, regras e atributos de qualidade são misturados na mesma frase (requisitos não-atômicos). A literatura recomenda separar rigorosamente:
1. Requisitos Funcionais (o que o sistema faz).
2. Requisitos de Qualidade (atributos como tempo, performance e segurança), que devem ser documentados separadamente e fazer referência ao requisito funcional.
3. Restrições (limitações tecnológicas, legais ou de negócio).
*(Nota: Pohl recomenda fortemente não utilizar o termo "requisitos não-funcionais", adotando as três categorias acima)*.

**C. O Padrão de Sentença Sintática (*Template* de Pohl)**
Para estruturar o requisito funcional final, deve-se adotar um *template* estrito composto por cinco elementos:
1.  **Condição (opcional):** Define quando a ação ocorre. Usa-se "Se" para condições lógicas ou "Assim que" / "Após" para condições temporais.
2.  **O Sistema (Sujeito):** O sujeito gramatical da sentença (o sistema ou módulo específico).
3.  **Verbo Modal (Obrigação):** Define a importância (DEVE/Shall para obrigatório, DEVERIA/Should para recomendado, PODE/May para opcional).
4.  **Ação / Processo:** O núcleo da funcionalidade, que deve se adequar a uma de três variações possíveis dependendo de como o sistema atua:
    *   *Atividade Autônoma:* O sistema atua sozinho. (Ex: *O sistema DEVE `<verbo de ação>`*).
    *   *Interação com Usuário:* O sistema atende a um ator. (Ex: *O sistema DEVE prover `<a quem?>` a capacidade de `<verbo de ação>`*).
    *   *Reativo / Interface:* O sistema reage a eventos. (Ex: *O sistema DEVE ser capaz de `<verbo de ação>`*).
5.  **Objeto e Detalhes:** A entidade que recebe a ação do sistema, acompanhada de detalhes estritamente necessários.