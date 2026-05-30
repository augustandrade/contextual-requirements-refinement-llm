Sim. O arquivo atual ainda está no modelo antigo: fala em *Goldset*, 20 instâncias, contexto rico/pobre, teste A/B e inclui termos como “requisitos livres de defeitos” e “smells” em trechos metodológicos . Abaixo está uma versão adaptada para as definições atuais.

---

# Corpus controlado

O corpus controlado desta pesquisa será composto por requisitos textuais selecionados da literatura de Engenharia de Requisitos e de estudos recentes sobre ambiguidades em requisitos. Os exemplos foram mantidos em inglês, idioma original das fontes consultadas, com o objetivo de preservar as ambiguidades linguísticas, sintáticas, referenciais, semânticas e pragmáticas presentes nos textos originais.

O corpus será organizado em quatro categorias de análise:

1. problemas estruturais e mistura de *concerns*;
2. ambiguidades linguísticas e sintáticas;
3. ambiguidades específicas de domínio ou contexto;
4. grupo de controle.

A versão consolidada do corpus será composta por 15 textos-base. Cada texto-base será executado em três condições de contexto:

* **C0 — Sem contexto**;
* **C1 — Contexto geral**;
* **C2 — Contexto resolutivo**.

Assim, o experimento será composto por:

```text
15 textos-base × 3 condições de contexto = 45 execuções experimentais
```

A distinção entre texto-base e instância experimental é importante para a metodologia. O texto-base corresponde ao requisito selecionado da literatura. A instância experimental corresponde à combinação entre esse requisito e uma condição específica de contexto.

---

# Condições de contexto

## C0 — Sem contexto

Na condição C0, o requisito textual será submetido ao sistema sem bloco contextual adicional.

Essa condição funcionará como linha de base, permitindo observar o que o sistema consegue identificar apenas a partir da estrutura linguística do requisito e do conhecimento geral do modelo. Espera-se que o sistema seja capaz de identificar ambiguidades e problemas textuais, mas evite resolver ambiguidades dependentes de informações específicas de domínio.

## C1 — Contexto geral

Na condição C1, o requisito será acompanhado de um contexto geral, contendo informações amplas sobre domínio, atores, ambiente operacional ou finalidade do sistema, mas sem incluir explicitamente a definição, regra de negócio ou restrição necessária para resolver a ambiguidade principal.

Essa condição permitirá avaliar se um contexto geral já contribui para melhorar a interpretação e a estruturação do requisito, ou se a ambiguidade permanece bloqueante. O objetivo é observar se o sistema utiliza informações contextuais de forma conservadora, sem introduzir inferências não sustentadas.

## C2 — Contexto resolutivo

Na condição C2, o requisito será acompanhado de um contexto resolutivo, contendo definições, regras de negócio ou restrições suficientes para orientar uma interpretação específica.

Essa condição permitirá avaliar se, quando a evidência contextual está explicitamente disponível, o sistema consegue utilizá-la adequadamente para reduzir ambiguidades e produzir uma estruturação textual mais clara e semanticamente explícita. Operações de concern separation e decomposition, quando necessárias, ocorrem dentro da estruturação final.

---

# Estrutura do contexto controlado

Nos casos C1 e C2, o contexto será representado em estrutura XML/Markdown com quatro blocos:

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

Os blocos terão a seguinte finalidade:

* **domain:** indicar o domínio, ambiente operacional, atores e escopo do sistema;
* **glossary:** definir termos, siglas, jargões e entidades relevantes;
* **business_rules:** registrar regras de negócio, políticas, critérios de decisão ou condições operacionais;
* **constraints:** registrar restrições técnicas, legais, organizacionais, operacionais ou de qualidade.

---

# Categoria 1 — Problemas estruturais e mistura de concerns

Esta categoria reúne requisitos que apresentam problemas de estruturação textual, como requisitos não atômicos, múltiplas ações na mesma sentença, mistura entre funcionalidade, atributo de qualidade e restrição, ou formulações em voz passiva que ocultam atores relevantes.

## REQ-01 — Mistura de função e qualidade

**Texto-base:**
*If the glass break detector of a window detects the pane has been damaged, the system shall inform the security service within 2 seconds at the latest.*

**Fonte:** Pohl (2025).

**Problema esperado:**
Mistura entre requisito funcional e requisito de qualidade temporal.

**Resultado esperado:**
O sistema deve separar o comportamento funcional — informar o serviço de segurança após detecção de dano — do atributo de qualidade temporal — comunicação em até 2 segundos.

---

## REQ-02 — Voz passiva e ator oculto

**Texto-base:**
*When a rejection order is received for a cancellation request, System-A must raise a web alert.*

**Fonte:** Veizaga et al. (2024).

**Problema esperado:**
Condição expressa em voz passiva, ocultando o ator ou sistema responsável por emitir a ordem de rejeição.

**Resultado esperado:**
O sistema deve identificar a omissão do ator. Em C2, se houver definição contextual do emissor da ordem, o requisito pode ser reestruturado com o ator explicitado. Em C0 ou C1, caso a evidência seja insuficiente, a omissão deve ser sinalizada.

---

## REQ-03 — Múltiplas ações no mesmo requisito

**Texto-base:**
*System-A must add System-B to their downstream systems and allow System-C to subscribe to the Reporting flow.*

**Fonte:** Veizaga et al. (2024).

**Problema esperado:**
Mais de uma ação na mesma sentença, indicando requisito não atômico.

**Resultado esperado:**
O sistema deve decompor o requisito em pelo menos dois requisitos menores e semanticamente independentes: um relacionado à adição de System-B aos sistemas downstream e outro relacionado à permissão para System-C assinar o fluxo de relatórios.

---

## REQ-04 — Parágrafo complexo com funcionalidade e restrição de design

**Texto-base:**
*The system must check for inconsistencies in account data between the Active Account Log and the Account Manager archive. The logic that is used to generate these comparisons should be based on the logic in the existing consistency checker tool. In other words, the new code does not need to be developed from scratch.*

**Fonte:** Wiegers; Beatty (2013).

**Problema esperado:**
Mistura entre funcionalidade, restrição de design/reuso e explicação em texto livre contínuo.

**Resultado esperado:**
O sistema deve separar o requisito funcional principal da restrição de design associada ao reaproveitamento da lógica existente.

---

# Categoria 2 — Ambiguidades linguísticas e sintáticas

Esta categoria reúne requisitos cuja dificuldade principal está na estrutura da linguagem natural, como pronomes vagos, construções sintáticas ambíguas, conectivos lógicos com precedência incerta e termos fracos ou pouco verificáveis.

## REQ-05 — Ambiguidade referencial de pronome

**Texto-base:**
*The customer inserts the access card into the card reader and enters a personal identification number (PIN) at the keypad. If it is invalid, the system shall deny the access.*

**Fonte:** Pohl (2025).

**Problema esperado:**
O pronome *it* pode se referir ao cartão de acesso ou ao PIN.

**Resultado esperado:**
O sistema deve identificar a ambiguidade referencial. Em C2, se o contexto fornecer regra suficiente para distinguir o comportamento associado ao cartão inválido e ao PIN inválido, o sistema deve selecionar a interpretação sustentada. Em C0 ou C1, caso a referência permaneça incerta, o sistema deve sinalizar a ambiguidade como bloqueante ou parcialmente bloqueante.

---

## REQ-06 — Ambiguidade sintática

**Texto-base:**
*The user enters the access card with the access code.*

**Fonte:** Pohl (2025).

**Problema esperado:**
Ambiguidade sobre a relação entre o cartão de acesso e o código de acesso: o código pode estar associado ao cartão ou pode ser uma informação inserida separadamente pelo usuário.

**Resultado esperado:**
O sistema deve listar as interpretações possíveis. Em C2, se houver regra contextual suficiente, deve reestruturar a sentença de forma inequívoca. Caso contrário, deve sinalizar a ambiguidade.

---

## REQ-07 — Ambiguidade lógica entre AND/OR

**Texto-base:**
*If a window of the car is damaged and the interior surveillance of the car detects an intruder or a door of the car is opened without a car key, the safety system shall raise an alarm.*

**Fonte:** Pohl (2025).

**Problema esperado:**
Precedência lógica incerta entre *and* e *or*.

**Resultado esperado:**
O sistema deve identificar que a condição pode ser interpretada de mais de uma forma. Em C2, caso uma regra de negócio defina a lógica condicional pretendida, o sistema deve reestruturar a condição com agrupamento explícito. Em C0 ou C1, se a regra permanecer indeterminada, deve sinalizar a ambiguidade.

---

## REQ-08 — Termo fraco ou obrigatoriedade ambígua

**Texto-base:**
*When leaving the Factory mode, the ECU should preferably perform a reset.*

**Fonte:** Unterbusch; Vogelsang (2026).

**Problema esperado:**
Uso de *should preferably*, tornando a obrigatoriedade fraca e pouco verificável.

**Resultado esperado:**
O sistema deve identificar que a obrigatoriedade não está claramente definida. Em C2, se o contexto especificar que o reset é obrigatório ou opcional em determinada condição, o requisito deve ser refinado com modalidade clara. Em C0 ou C1, a indefinição deve ser sinalizada.

---

# Categoria 3 — Ambiguidades específicas de domínio ou contexto

Esta categoria reúne requisitos cuja interpretação depende fortemente de informações específicas de domínio, regras operacionais ou restrições técnicas. Esses casos são especialmente relevantes para avaliar a etapa de validação de resolubilidade contextual.

## REQ-09 — Medição contínua

**Texto-base:**
*Shut off the pumps if the water level remains above 100 meters for more than 4 seconds.*

**Fonte:** Kamsties (2001).

**Problema esperado:**
Ambiguidade sobre como avaliar a medição contínua ao longo da janela temporal: valor mínimo, valor médio, mediana, valor instantâneo ou outra métrica.

**Resultado esperado:**
O sistema deve identificar que a regra de avaliação da medição contínua não está explicitada. Em C2, se o contexto definir a métrica de avaliação, o requisito pode ser reestruturado. Em C0 ou C1, a ambiguidade deve ser sinalizada como bloqueante.

---

## REQ-10 — Vagueza de fronteira

**Texto-base:**
*All medium-sized vehicles shall be equipped with a navigation system.*

**Fonte:** Pohl (2025).

**Problema esperado:**
Ausência de fronteira objetiva para o termo *medium-sized*.

**Resultado esperado:**
O sistema deve identificar a vagueza de fronteira. Em C2, caso o contexto defina a faixa objetiva de peso ou categoria, o requisito deve ser refinado. Em C0 ou C1, deve sinalizar que a definição está ausente.

---

## REQ-11 — Ambiguidade pragmática de aplicação

**Texto-base:**
*Generate a dial tone.*

**Fonte:** Kamsties (2001).

**Problema esperado:**
Especificação insuficiente, pois o tom de discagem depende do padrão de telecomunicação adotado.

**Resultado esperado:**
O sistema deve identificar a insuficiência da especificação. Em C2, caso o contexto indique o padrão aplicável, o requisito deve ser refinado com os parâmetros correspondentes. Em C0 ou C1, deve sinalizar a lacuna contextual.

---

## REQ-12 — Lacuna técnica operacional

**Texto-base:**
*Routing switches ability to filter network traffic between data-plane interfaces and management data traffic.*

**Fonte:** Bashir et al. (2025).

**Problema esperado:**
Formulação incompleta e ambígua quanto ao tipo de filtragem, às interfaces envolvidas e ao significado de *management data traffic*.

**Resultado esperado:**
O sistema deve identificar lacunas técnicas e problemas de formulação. Em C2, caso o contexto defina os termos técnicos e a forma de filtragem esperada, o requisito pode ser reestruturado. Em C0 ou C1, deve sinalizar as informações ausentes.

---

# Categoria 4 — Grupo de controle

Esta categoria reúne requisitos sem problemas estruturais relevantes esperados. O objetivo é verificar se o sistema preserva requisitos já adequadamente estruturados, evitando alterações desnecessárias ou degradação da especificação.

## REQ-13 — Requisito funcional em estrutura controlada

**Texto-base:**
*If an 'Instruction' contains a 'Keyword', The User must upload the 'excel file' to System-A.*

**Fonte:** Veizaga et al. (2024).

**Problema esperado:**
Nenhum problema estrutural relevante esperado.

**Resultado esperado:**
O sistema deve preservar a estrutura do requisito, realizando no máximo ajustes formais mínimos. A variação entre C0, C1 e C2 deve permitir observar se o contexto provoca alterações desnecessárias em um requisito já estruturado.

---

## REQ-14 — Requisito funcional já separado

**Texto-base:**
*R-F-18: If the detector detects damage to the pane, the system shall inform the security service.*

**Fonte:** Pohl (2025).

**Problema esperado:**
Requisito funcional já isolado.

**Resultado esperado:**
O sistema deve preservar a estrutura funcional do requisito.

---

## REQ-15 — Requisito de qualidade já isolado

**Texto-base:**
*R-Q-2: The system shall inform the security service within 2 s after detecting damage.*

**Fonte:** Pohl (2025).

**Problema esperado:**
Requisito de qualidade já separado do requisito funcional correspondente.

**Resultado esperado:**
O sistema deve preservar o requisito como requisito de qualidade e, quando aplicável, manter a relação semântica com o requisito funcional correspondente.

---

# Referência manual de comparação

Para apoiar a avaliação qualitativa, será elaborada uma referência manual de comparação para cada uma das 45 execuções experimentais. Essa referência manual funcionará como gabarito qualitativo e indicará o comportamento esperado do sistema diante de cada condição de contexto.

A referência manual conterá:

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

---

# Uso dos resultados no TCC

Os resultados completos das 45 execuções experimentais serão armazenados em repositório Git, juntamente com os *prompts*, contextos controlados, registros intermediários e saídas completas do sistema. No corpo do TCC, serão apresentados apenas os resultados mais relevantes para a discussão, em formato de tabelas e exemplos selecionados.

A apresentação dos resultados deverá incluir, preferencialmente:

* uma tabela geral com a síntese das 45 execuções;
* exemplos detalhados de casos resolúveis;
* exemplos detalhados de ambiguidades bloqueantes;
* exemplos de refinamento parcial;
* exemplos do grupo de controle;
* ao menos um caso de resultado parcialmente adequado ou inadequado, para sustentar a análise crítica.

---

Essa versão já substitui a lógica antiga do arquivo — *Goldset*, 20 instâncias, contexto rico/pobre e teste A/B — por uma estrutura compatível com sua metodologia atual: **corpus controlado, 15 textos-base, três níveis de contexto e 45 execuções experimentais**.
