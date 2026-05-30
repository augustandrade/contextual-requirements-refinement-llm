## Agente 3 — Estruturador de Requisitos

### Função central

O Agente 3 deve produzir a **saída estruturada final do requisito**, utilizando:

* o requisito original;
* o contexto controlado, quando houver;
* a análise de resolubilidade contextual do Agente 2, **somente quando a execução tiver sido classificada como `fully_resolvable` ou `no_ambiguity`**.

A pergunta central dele é:

> Dado o grau de resolubilidade definido pelo Agente 2, qual é a melhor estruturação segura para este requisito?

Ele pode refinar, estruturar e explicitar informações sustentadas, mas só quando a execução tiver passado pela orquestração que autoriza sua chamada.

---

## O que o Agente 3 deve receber

A entrada deve reunir o estado acumulado da execução:

```yaml
execution_input:

  base_requirement_text: ""

  controlled_context:
    available: true | false
    domain: ""
    glossary: []
    business_rules: []
    constraints: []

  contextual_resolubility_validation:
    ambiguity_resolubility: []
    overall_resolubility:
      status: "fully_resolvable | unresolved | no_ambiguity"
      explanation: ""
```

Orchestration note:
- The orchestrator SHALL call the `requirement_structurer` (Agent 3) only when `overall_resolubility.status` is `fully_resolvable` or `no_ambiguity`.
- If `overall_resolubility.status` is `unresolved`, the orchestrator MUST bypass Agent 3 and route the execution to the alternative formatting/review path.
- Agent 3 does not receive unresolved executions.

O campo mais importante vindo do Agente 2 é:

```yaml
allowed_structuring_action:
  - use_supported_interpretation
  - flag_for_human_clarification
  - no_action_needed
```

Esse campo deve controlar o comportamento do estruturador quando ele for chamado.

---

## Instruções principais do Agente 3

O Agente 3 deve:

1. produzir uma versão estruturada do requisito;
2. usar interpretações sustentadas quando o Agente 2 indicar `resolvable`;
3. classificar a saída como requisito funcional, requisito de qualidade ou restrição;
4. explicitar termos, condições, atores e objetos quando houver evidência;
5. evitar inferências não sustentadas;
6. registrar ambiguidades que permaneçam relevantes mesmo após a estruturação;
7. preservar requisitos de controle quando não houver problema relevante.

Ele não deve:

* receber ou tratar casos `unresolved`;
* resolver ambiguidade sem evidência suficiente;
* escolher interpretação por plausibilidade;
* usar conhecimento externo;
* inventar ator, métrica, prazo, condição, objeto ou regra de negócio;
* forçar template funcional para requisito de qualidade ou restrição;
* transformar toda observação em requisito se não houver evidência.

---

## Regra decisória principal

A estruturação deve seguir esta lógica:

| Status do Agente 2     | Comportamento do Agente 3                                  |
| ---------------------- | ---------------------------------------------------------- |
| `resolvable`           | Usar a interpretação sustentada e estruturar o requisito   |
| `no_ambiguity`          | Preservar ou estruturar normalmente, sem inventar problema |
| `unresolved`           | Não recebe a execução; rota alternativa deve ser usada    |

A frase-chave do prompt deve ser:

> Do not resolve what the contextual resolubility validator classified as unresolved.

---

## Como aplicar Pohl sem exagerar o escopo

O Agente 3 deve usar Pohl como referência de estruturação, não como uma camisa de força.

Para **requisitos funcionais**, ele deve tentar extrair:

```yaml
condition:
condition_type:
system_or_component:
interaction_pattern:
actor:
modality:
action:
object:
final_statement:
```

As variações de interação podem ser:

```yaml
interaction_pattern:
  - autonomous_system_activity
  - user_interaction
  - external_interface_or_reactive_behavior
```

Exemplos de forma:

* Atividade autônoma:
  `The system shall <action> <object>.`

* Interação com usuário:
  `The system shall provide <actor> with the ability to <action> <object>.`

* Comportamento reativo/interface:
  `The system shall be able to <action> <object>.`

Para **requisitos de qualidade**, não forçar o template funcional. Usar algo como:

```yaml
type: quality_requirement
related_functional_requirement:
quality_attribute:
measurable_criterion:
condition:
final_statement:
```

Para **restrições**, usar:

```yaml
type: constraint
constraint_category:
affected_element:
constraint_statement:
rationale_or_source:
final_statement:
```

---

## Como lidar com separação de tipos e múltiplas ações

Como o novo escopo não avalia *concerns* e atomicidade como critérios independentes, o Agente 3 deve tratar isso como **operação auxiliar**.

Instrução sugerida:

> If the original requirement combines multiple actions or mixes functionality, quality attributes, and constraints, separate them only when necessary to produce a clear and safe final structure. Do not treat decomposition or concern separation as independent goals.

Assim ele pode gerar mais de um requisito estruturado quando necessário, mas sem transformar isso no foco do TCC.

---

## Saída esperada do Agente 3

Sugiro este schema:

```yaml
requirement_structuring:
  execution_id: "REQ-XX-CX"
  requirement_id: "REQ-XX"
  context_condition: "C0 | C1 | C2"

  structuring_summary: ""

  structured_requirements:
    - structured_id: "REQ-XX-SR-01"
      type: "functional_requirement | quality_requirement | constraint | unresolved_requirement"

      source_fragments:
        - ""

      based_on_resolubility:
        ambiguity_ids:
          - "AMB-01"
        applied_action: "use_supported_interpretation | flag_for_human_clarification | no_action_needed"

      fields:
        condition: ""
        condition_type: "logical | temporal | event | none"
        system_or_component: ""
        interaction_pattern: "autonomous_system_activity | user_interaction | external_interface_or_reactive_behavior | not_applicable"
        actor: ""
        modality: "shall | should | may | unspecified"
        action: ""
        object: ""
        quality_attribute: ""
        measurable_criterion: ""
        constraint_category: ""
        affected_element: ""

      final_statement: ""

      structuring_notes:
        - ""

  unresolved_ambiguities:
    - ambiguity_id: "AMB-XX"
      fragment: ""
      reason: ""
      missing_information:
        - ""
      suggested_clarification_question: ""

  preserved_uncertainties:
    - ""

  unsupported_inferences_avoided:
    - ""

  final_output_status: "structured | partially_structured | preserved"
```

---

## Campos essenciais

Se quiser manter mais simples, os campos indispensáveis são:

```yaml
structured_requirements:
  - structured_id:
    type:
    source_fragments:
    based_on_resolubility:
    fields:
      condition:
      system_or_component:
      actor:
      modality:
      action:
      object:
    final_statement:
    structuring_notes:

unresolved_ambiguities:
  - ambiguity_id:
    reason:
    missing_information:
    suggested_clarification_question:

final_output_status:
```

Isso já é suficiente para avaliação qualitativa.

---

## Prompt conceitual do Agente 3

```text
You are a requirement structuring agent specialized in natural language requirements.

Your task is to produce a structured version of the requirement using the original requirement text, the controlled context, and the contextual resolubility validation.

You must follow the resolubility decisions produced by the previous agent.

If an ambiguity is resolvable, use only the supported interpretation indicated by the contextual resolubility validator.

If there is no ambiguity, preserve or minimally structure the requirement without introducing new information.

If the execution is unresolved, do not produce Agent 3 output; the orchestrator must use the alternative formatting/review route.

Use only the original requirement and the controlled context as evidence. Do not use external knowledge. Do not invent actors, business rules, metrics, thresholds, conditions, or technical constraints.

Apply requirement structuring principles inspired by Pohl:
- classify the output as functional requirement, quality requirement, or constraint;
- for functional requirements, use a controlled sentence structure with condition, system/component, modality, action, object, and actor when applicable;
- do not force the functional template onto quality requirements or constraints;
- if multiple actions or mixed requirement types appear, separate them only when necessary for a clear and safe final structure.

Return the output in the required structured format.
```

---

## Recomendação final

Eu definiria o Agente 3 como:

**Nome:** `requirement_structurer`

**Função:** gerar a estrutura final segura do requisito.

**Entrada:** requisito + contexto + resolubilidade contextual apenas quando `overall_resolubility.status` for `fully_resolvable` ou `no_ambiguity`.

**Saída:** requisitos estruturados + ambiguidades não resolvidas que ainda sobraram na estrutura + status final.

**Não faz:** nova detecção de ambiguidades, nova validação de resolubilidade ou inferência externa.

**Regra central:** ele só pode estruturar com base no que foi autorizado pela resolubilidade contextual, e não recebe casos `unresolved`.

Com isso, o pipeline fica conceitualmente bem fechado:

```text
Agente 1: O que está ambíguo?
Agente 2: Pode seguir para estruturação ou precisa de rota alternativa?
Agente 3: Como estruturar o requisito quando a execução é segura?
Módulo Python: Como consolidar e salvar o resultado?
```
