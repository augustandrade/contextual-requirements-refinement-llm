# Contexto controlado e corpus experimental

O contexto controlado deste trabalho foi definido como uma estrutura textual padronizada utilizada para fornecer ao sistema informações adicionais sobre o domínio, os termos, as regras de negócio e as restrições associadas a cada requisito. Como diferentes tipos de ambiguidades e problemas textuais exigem diferentes recortes de conhecimento para serem analisados, o contexto foi organizado em blocos explícitos, permitindo controlar o grau de informação fornecido ao modelo.

A estruturação do contexto é relevante porque a interpretação de requisitos escritos em linguagem natural pode depender de informações que não estão presentes no próprio requisito, mas que fazem parte do domínio, do ambiente operacional ou das convenções compartilhadas entre os envolvidos. Assim, o contexto controlado foi utilizado como mecanismo de explicitação semântica, permitindo avaliar em que medida diferentes níveis de informação contextual influenciam a identificação, a resolubilidade e o refinamento de requisitos textuais.

## Estrutura do contexto controlado

O contexto controlado foi padronizado em quatro blocos principais:

**1. Domínio (`domain`)**
Descrição breve do escopo do sistema, ambiente operacional, atores envolvidos e processo de negócio relacionado ao requisito.

**2. Glossário (`glossary`)**
Definições de termos técnicos, siglas, entidades, jargões, sinônimos ou significados específicos do domínio.

**3. Regras de negócio (`business_rules`)**
Políticas, critérios de decisão, regras operacionais ou lógicas de negócio que orientam a interpretação do requisito.

**4. Restrições (`constraints`)**
Limitações técnicas, legais, organizacionais, operacionais ou de qualidade impostas ao sistema.

O formato adotado para o contexto controlado utiliza marcações em XML/Markdown, com o objetivo de separar claramente cada categoria de informação fornecida ao modelo. Essa estrutura facilita a rastreabilidade da informação contextual utilizada durante a execução do pipeline. Nas execuções experimentais, o bloco `<controlled_context>` é injetado apenas nas condições C1 e C2.

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

## Níveis de contexto utilizados no experimento

Para reduzir o viés de fornecer ao modelo apenas um contexto diretamente resolutivo, o delineamento experimental passou a considerar três níveis de contexto. Essa decisão permite avaliar não apenas se o contexto melhora o refinamento, mas também em que medida diferentes graus de explicitação contextual influenciam a análise do requisito.

### C0 — Sem contexto

Na condição C0, o requisito textual é submetido ao sistema sem bloco contextual adicional. Operacionalmente, essa condição corresponde a `inject_context: false`, isto é, sem envio do bloco `<controlled_context>` para o modelo.

Essa condição funciona como linha de base, permitindo observar o que o sistema consegue identificar apenas a partir da estrutura linguística do requisito e do conhecimento geral do modelo. Espera-se que, nessa condição, o sistema seja capaz de detectar ambiguidades e problemas textuais, mas evite resolver ambiguidades que dependem de informações específicas de domínio.

### C1 — Contexto geral

Na condição C1, o requisito é acompanhado de um contexto geral, contendo informações amplas sobre o domínio, atores, ambiente operacional ou finalidade do sistema, mas sem incluir explicitamente a regra ou definição necessária para resolver a ambiguidade principal. Operacionalmente, essa condição corresponde a `inject_context: true`.

Essa condição permite verificar se um contexto geral já é suficiente para melhorar a interpretação e a estruturação do requisito ou se a ambiguidade permanece bloqueante. O objetivo é observar se o sistema utiliza o contexto de forma conservadora, sem introduzir inferências não sustentadas.

### C2 — Contexto resolutivo

Na condição C2, o requisito é acompanhado de um contexto resolutivo, contendo definições, regras de negócio ou restrições suficientes para orientar uma interpretação específica. Operacionalmente, essa condição corresponde a `inject_context: true`.

Essa condição permite avaliar se, quando a evidência contextual está explicitamente disponível, o sistema consegue utilizá-la adequadamente para reduzir ambiguidades e produzir uma estruturação textual mais clara e semanticamente explícita. Operações de concern separation e decomposition, quando necessárias, ocorrem dentro da estruturação final.

## Corpus controlado

O corpus controlado foi definido como o conjunto de requisitos textuais selecionados da literatura de Engenharia de Requisitos e de estudos recentes sobre ambiguidades em requisitos. Os requisitos foram mantidos no idioma original das fontes, majoritariamente em inglês, com o objetivo de preservar as ambiguidades linguísticas, sintáticas, referenciais e semânticas discutidas na literatura. A tradução dos requisitos poderia alterar o fenômeno linguístico analisado, criando ou removendo ambiguidades relevantes para o estudo.

O corpus foi organizado em quatro categorias de análise:

1. problemas estruturais e mistura de *concerns*;
2. ambiguidades linguísticas e sintáticas;
3. ambiguidades específicas de domínio ou contexto;
4. requisitos de controle sem problemas estruturais relevantes esperados.

A versão consolidada do corpus será composta por 15 textos-base. Cada texto-base será submetido a três condições de contexto — C0, C1 e C2 — totalizando 45 execuções experimentais.

```text
15 textos-base × 3 condições de contexto = 45 execuções experimentais
```

## Categorias de análise do corpus

### Categoria 1 — Problemas estruturais e mistura de *concerns*

Esta categoria reúne requisitos que apresentam problemas de estruturação textual, como requisitos não atômicos, múltiplas ações em uma mesma sentença, mistura entre funcionalidade, atributo de qualidade e restrição, ou formulações em voz passiva que ocultam atores relevantes.

Exemplos previstos:

1. **REQ-01 — Mistura de função e qualidade**
   *If the glass break detector of a window detects the pane has been damaged, the system shall inform the security service within 2 seconds at the latest.*
   Fonte: Pohl (2025).
   Problema esperado: mistura entre requisito funcional e atributo de qualidade temporal.

2. **REQ-02 — Voz passiva e ator oculto**
   *When a rejection order is received for a cancellation request, System-A must raise a web alert.*
   Fonte: Veizaga et al. (2024).
   Problema esperado: condição em voz passiva, com ator emissor da ordem não explicitado.

3. **REQ-03 — Múltiplas ações no mesmo requisito**
   *System-A must add System-B to their downstream systems and allow System-C to subscribe to the Reporting flow.*
   Fonte: Veizaga et al. (2024).
   Problema esperado: mais de uma ação na mesma sentença, indicando requisito não atômico.

4. **REQ-04 — Parágrafo complexo com funcionalidade e restrição de design**
   *The system must check for inconsistencies in account data between the Active Account Log and the Account Manager archive. The logic that is used to generate these comparisons should be based on the logic in the existing consistency checker tool. In other words, the new code does not need to be developed from scratch.*
   Fonte: Wiegers; Beatty (2013).
   Problema esperado: mistura de funcionalidade, restrição de design e explicação em texto livre.

### Categoria 2 — Ambiguidades linguísticas e sintáticas

Esta categoria reúne requisitos cuja dificuldade principal está na própria estrutura da linguagem natural, como pronomes vagos, construções sintáticas ambíguas, conectivos lógicos com precedência incerta e termos fracos ou pouco verificáveis.

Exemplos previstos:

5. **REQ-05 — Ambiguidade referencial de pronome**
   *The customer inserts the access card into the card reader and enters a personal identification number (PIN) at the keypad. If it is invalid, the system shall deny the access.*
   Fonte: Pohl (2025).
   Problema esperado: o pronome *it* pode se referir ao cartão de acesso ou ao PIN.

6. **REQ-06 — Ambiguidade sintática**
   *The user enters the access card with the access code.*
   Fonte: Pohl (2025).
   Problema esperado: ambiguidade sobre a relação entre o cartão de acesso e o código de acesso.

7. **REQ-07 — Ambiguidade lógica entre AND/OR**
   *If a window of the car is damaged and the interior surveillance of the car detects an intruder or a door of the car is opened without a car key, the safety system shall raise an alarm.*
   Fonte: Pohl (2025).
   Problema esperado: precedência lógica incerta entre *and* e *or*.

8. **REQ-08 — Termo fraco ou obrigatoriedade ambígua**
   *When leaving the Factory mode, the ECU should preferably perform a reset.*
   Fonte: Unterbusch; Vogelsang (2026).
   Problema esperado: uso de *should preferably*, tornando a obrigatoriedade fraca e pouco verificável.

### Categoria 3 — Ambiguidades específicas de domínio ou contexto

Esta categoria reúne requisitos cuja interpretação depende fortemente de informações específicas do domínio, regras operacionais ou restrições técnicas. Esses casos são especialmente relevantes para avaliar a etapa de validação de resolubilidade contextual.

Exemplos previstos:

9. **REQ-09 — Medição contínua**
   *Shut off the pumps if the water level remains above 100 meters for more than 4 seconds.*
   Fonte: Kamsties (2001).
   Problema esperado: ambiguidade sobre como avaliar a medição contínua ao longo da janela temporal.

10. **REQ-10 — Vagueza de fronteira**
    *All medium-sized vehicles shall be equipped with a navigation system.*
    Fonte: Pohl (2025).
    Problema esperado: ausência de fronteira objetiva para o termo *medium-sized*.

11. **REQ-11 — Ambiguidade pragmática de aplicação**
    *Generate a dial tone.*
    Fonte: Kamsties (2001).
    Problema esperado: especificação insuficiente, pois o tom de discagem depende do padrão de telecomunicação adotado.

12. **REQ-12 — Lacuna técnica operacional**
    *Routing switches ability to filter network traffic between data-plane interfaces and management data traffic.*
    Fonte: Bashir et al. (2025).
    Problema esperado: formulação incompleta e ambígua quanto ao tipo de filtragem, interfaces envolvidas e significado de *management data traffic*.

### Categoria 4 — Grupo de controle

Esta categoria reúne requisitos sem problemas estruturais relevantes esperados. O objetivo é verificar se o sistema preserva requisitos já adequadamente estruturados, evitando alterações desnecessárias ou degradação da especificação.

Exemplos previstos:

13. **REQ-13 — Requisito funcional em estrutura controlada**
    *If an 'Instruction' contains a 'Keyword', The User must upload the 'excel file' to System-A.*
    Fonte: Veizaga et al. (2024).
    Problema esperado: nenhum problema estrutural relevante esperado.

14. **REQ-14 — Requisito funcional já separado**
    *R-F-18: If the detector detects damage to the pane, the system shall inform the security service.*
    Fonte: Pohl (2025).
    Problema esperado: requisito funcional já isolado.

15. **REQ-15 — Requisito de qualidade já isolado**
    *R-Q-2: The system shall inform the security service within 2 s after detecting damage.*
    Fonte: Pohl (2025).
    Problema esperado: requisito de qualidade já separado do requisito funcional correspondente.

## Instâncias experimentais

Cada um dos 15 textos-base será executado em três condições de contexto:

* **C0 — Sem contexto**;
* **C1 — Contexto geral**;
* **C2 — Contexto resolutivo**.

Assim, cada execução experimental será composta por:

```text
texto-base + condição de contexto
```

Regra operacional de execução:

* C0: enviar apenas o texto-base;
* C1: enviar texto-base + `<controlled_context>` geral;
* C2: enviar texto-base + `<controlled_context>` resolutivo.

A distinção entre texto-base e instância experimental é importante para evitar confusão metodológica. O texto-base corresponde ao requisito selecionado da literatura. A instância experimental corresponde à combinação entre esse requisito e um nível específico de contexto.

## Referência manual de comparação

Para apoiar a avaliação qualitativa, será elaborada uma referência manual de comparação para cada uma das 45 execuções experimentais. Essa referência manual funcionará como gabarito qualitativo e indicará o comportamento esperado do sistema diante de cada condição de contexto.

A referência manual deverá conter:

```markdown
ID da execução:
Texto-base:
Condição de contexto: C0 | C1 | C2
Problema esperado:
Ambiguidades esperadas:
Interpretações possíveis:
Resolubilidade esperada: resolúvel | parcialmente resolúvel | bloqueante | não aplicável
Ação esperada do sistema:
- preservar
- refinar
- decompor
- separar concerns
- sinalizar bloqueio
Saída esperada resumida:
Critérios de avaliação aplicáveis:
```

## Uso dos resultados no TCC

Os resultados completos das 45 execuções experimentais serão armazenados em repositório Git, juntamente com os *prompts*, contextos controlados, registros intermediários e saídas completas do sistema. No corpo do TCC, serão apresentados apenas os resultados mais relevantes para a discussão, em formato de tabelas e exemplos selecionados.

A apresentação dos resultados deverá incluir, preferencialmente:

* uma tabela geral com o desempenho do sistema nas 45 execuções;
* exemplos detalhados de casos resolúveis;
* exemplos detalhados de ambiguidades bloqueantes;
* exemplos de refinamento parcial;
* exemplos do grupo de controle;
* ao menos um caso de resultado parcialmente adequado ou inadequado, para sustentar a análise crítica.

---

Essa versão corrige o ponto central do texto anterior: ele ainda falava em **20 instâncias**, **10 textos-base**, *goldset*, **contexto rico/pobre** e teste A/B . Agora, a lógica fica alinhada à sua decisão atual: **15 textos-base, 3 níveis de contexto, 45 execuções experimentais, corpus controlado e referência manual de comparação**.
