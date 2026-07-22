# Apêndice B — Corpus Controlado: Requisitos de Linguagem Natural

Os 14 requisitos que compõem o corpus foram elaborados pelo autor com base em exemplos e padrões recorrentes na literatura de Engenharia de Requisitos. Os textos dos requisitos, os contextos controlados e os gabaritos de avaliação (`manual_reference`) estão disponíveis integralmente em Andrade (2026).

---

## Cat-01 — Estrutural (REQ-01 a REQ-03)

Requisitos que apresentam "concern mixing" entre preocupações funcionais e de qualidade, ou que combinam múltiplas ações em um único enunciado, exigindo estruturação para garantir atomicidade (Pohl, 2025).

| ID | Requisito | Problema esperado |
|---|---|---|
| REQ-01 | If the glass break detector of a window detects the pane has been damaged, the system shall inform the security service within 2 seconds at the latest. | Comportamento funcional e critério de qualidade temporal misturados em um único enunciado. |
| REQ-02 | When a rejection order is received for a cancellation request, System-A must raise a web alert. | Construção passiva oculta o ator responsável pela emissão da ordem de rejeição. |
| REQ-03 | System-A must add System-B to their downstream systems and allow System-C to subscribe to the Reporting flow. | Duas ações distintas em um único enunciado — exige estruturação para preservar ambas. |

---

## Cat-02 — Linguística (REQ-04 a REQ-07)

Requisitos com ambiguidades sintáticas, lexicais, referenciais ou de vaguidade. A resolubilidade varia conforme o contexto fornecido ao pipeline.

| ID | Requisito | Problema esperado |
|---|---|---|
| REQ-04 | The customer inserts the access card into the card reader and enters a personal identification number (PIN) at the keypad. If it is invalid, the system shall deny the access. | O pronome "it" pode se referir ao cartão de acesso ou ao PIN — ambiguidade referencial. |
| REQ-05 | The user enters the access card with the access code. | "with the access code" pode descrever o cartão ou uma ação separada do usuário — ambiguidade sintática de adjunção. |
| REQ-06 | If a window of the car is damaged and the interior surveillance of the car detects an intruder or a door of the car is opened without a car key, the safety system shall raise an alarm. | Agrupamento lógico ambíguo pela precedência de "and"/"or" — ambiguidade sintática. |
| REQ-07 | When leaving the Factory mode, the ECU should preferably perform a reset. | "should preferably" cria obrigação fraca e não verificável — vaguidade. |

---

## Cat-03 — Domínio (REQ-08 a REQ-11)

Requisitos cujas ambiguidades dependem de conhecimento especializado ou de parâmetros técnicos ausentes no texto — não detectáveis sem consciência da lacuna definitória.

| ID | Requisito | Problema esperado |
|---|---|---|
| REQ-08 | Shut off the pumps if the water level remains above 100 meters for more than 4 seconds. | Falta de regra para avaliação de medição contínua dentro da janela de tempo definida. |
| REQ-09 | All medium-sized vehicles shall be equipped with a navigation system. | "medium-sized" não possui limite objetivo definido no domínio. |
| REQ-10 | Generate a dial tone. | Parâmetros do tom de discagem dependem do padrão de telecomunicações e da região de operação. |
| REQ-11 | Routing switches ability to filter network traffic between data-plane interfaces and management data traffic. | Definições técnicas incompletas para o comportamento de filtragem e o escopo do tráfego de gerenciamento. |

---

## Cat-04 — Controle (REQ-12 a REQ-14)

Requisitos intencionalmente livres de ambiguidades linguísticas. REQ-13 e REQ-14 correspondem aos sub-requisitos resultantes da decomposição correta de REQ-01, produto esperado do pipeline para "concern mixing".

| ID | Requisito | Observação |
|---|---|---|
| REQ-12 | If an 'Instruction' contains a 'Keyword', The User must upload the 'excel file' to System-A. | Requisito funcional sem defeito esperado — grupo de controle. |
| REQ-13 | R-F-18: If the detector detects damage to the pane, the system shall inform the security service. | Requisito funcional já isolado — sub-requisito de REQ-01 corretamente separado. |
| REQ-14 | R-Q-2: The system shall inform the security service within 2 s after detecting damage. | Requisito de qualidade já isolado — sub-requisito de REQ-01 corretamente separado. |

---

## Rodada-piloto (REQ-PILOT-01 a REQ-PILOT-04)

Os quatro requisitos utilizados na execução-piloto foram elaborados pelo autor com base em padrões recorrentes na literatura de Engenharia de Requisitos. A rodada-piloto precedeu a construção do corpus principal e orientou o ajuste dos prompts e a definição das categorias de defeito adotadas.

| ID | Requisito | Tipo de caso |
|---|---|---|
| REQ-PILOT-01 | When a customer submits an order, the system shall send a confirmation email to the customer within 30 seconds. | "Concern mixing" — ação funcional com restrição de entrega combinadas em uma única sentença. |
| REQ-PILOT-02 | The nurse administers the prescribed medication to the patient. If she does not respond within 10 minutes, the system shall escalate the alert to the duty physician. | Ambiguidade referencial — pronome com dois antecedentes concorrentes. |
| REQ-PILOT-03 | The system shall automatically approve the leave request if the employee is eligible. | Ambiguidade de domínio — critério de elegibilidade sem definição mensurável. |
| REQ-PILOT-04 | When the user selects the Save option, the system shall write the current document to disk and display a confirmation message. | Grupo de controle — requisito sem defeito esperado. |
