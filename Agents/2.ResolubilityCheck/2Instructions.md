## Agente 2 — Validador de Resolubilidade Contextual

### 1. Função do agente

O Agente 2 recebe o requisito original, o contexto da execução e a lista de ambiguidades detectadas pelo Agente 1. Sua função é avaliar, para cada ambiguidade, se existe evidência suficiente para o estruturador adotar uma interpretação sem inferência indevida.

Em outras palavras, ele responde:

> O próximo passo pode estruturar este ponto com segurança, usando apenas evidência disponível?

Ele não deve reescrever o requisito, nem produzir a saída final. Sua saída orienta a orquestração sobre duas rotas possíveis: a rota de estruturação pelo Agente 3 quando houver segurança interpretativa suficiente, ou a rota alternativa de formatação/revisão quando a ambiguidade permanecer unresolved.

---

## 2. O que o agente deve receber

Entrada prescrita: O Agente 2 deve receber como entrada a SAÍDA do Agente 1 (`ambiguity_detection`) juntamente com o `base_requirement_text` e, quando aplicável, o `controlled_context`. Em outras palavras, o payload encaminhado ao Agente 2 deve conter: (1) o texto-base do requisito, (2) o bloco `controlled_context` se a condição experimental for C1/C2, e (3) o bloco `ambiguity_detection` tal como produzido pelo Agente 1. Isso garante que o validador opere somente sobre evidências previamente coletadas.

Exemplo de payload:

```yaml
execution_input:
  base_requirement_text: ""

  controlled_context:
    available: true | false
    domain: ""
    glossary: []
    business_rules: []
    constraints: []

  ambiguity_detection:   # must be the exact structure returned by Agent 1
    has_ambiguity: true | false
    ambiguity_count: 0
    ambiguities:
      - ambiguity_id: "AMB-01"
        fragment: ""
        ambiguity_type: "lexical | syntactic | semantic | referential | logical | pragmatic_contextual"
        explanation: ""
        possible_interpretations:
          - ""
        textual_evidence:
          - ""
        context_evidence:
          - ""
        context_dependency: "none | low | moderate | high"
```

O mais importante é que ele receba **todas as ambiguidades do requisito em uma única chamada**, para manter a visão do requisito inteiro.

---

## 3. O que precisa estar nas instruções

As instruções devem deixar claro que o agente opera por **evidência**, não por plausibilidade.

Ele deve avaliar:

* se o requisito original sustenta alguma interpretação;
* se o contexto controlado sustenta alguma interpretação;
* se há lacuna relevante;
* se seria necessário conhecimento externo;
* se a ambiguidade afeta a estruturação final;
* se a execução pode seguir para o Agente 3;
* ou se a execução deve seguir para a rota alternativa de formatação final.

Ele não deve:

* reescrever o requisito;
* produzir requisito final;
* escolher interpretação por senso comum;
* usar conhecimento externo;
* assumir que C0 é sempre bloqueante;
* assumir que C2 é sempre resolvível;
* inventar regra de negócio, ator, métrica, prazo ou definição;
* alterar as ambiguidades detectadas pelo Agente 1.

---

## 4. Categorias de resolubilidade

### `resolvable`

Use quando há evidência suficiente no requisito ou no contexto para o estruturador adotar uma interpretação específica com segurança.

Regra prática:

> A interpretação adotada é X, porque o requisito ou o contexto afirma Y.

Exemplo:

```yaml
resolubility_status: "resolvable"
allowed_structuring_action: "use_supported_interpretation"
```

---

### `unresolved`

Use quando a ambiguidade não pode ser eliminada com segurança. Nesse caso, o requisito não segue para o Agente 3. Em vez disso, a orquestração deve acionar a rota alternativa para estruturar/formatar a saída final sem inferência automática adicional. Dependendo do caso, pode ainda ser possível descrever parte do requisito com segurança, ou pode não ser possível descrever nada além da própria incerteza.

Regra prática:

> Parte do requisito pode ser descrita com base em X, mas ainda falta Y para eliminar a ambiguidade com segurança. Em casos mais fortes, nada pode ser descrito com segurança além da constatação de que a informação falta.

Exemplo:

```yaml
resolubility_status: "unresolved"
allowed_structuring_action: "flag_for_human_clarification"
```

---

### `not_applicable`

Use quando não há ambiguidade relevante a validar.

Exemplo:

```yaml
resolubility_status: "not_applicable"
allowed_structuring_action: "no_action_needed"
```

---

## 5. Regra central do agente

Esta é a regra mais importante:

> A resolubilidade contextual não indica se o sistema produzirá uma saída, mas se há evidência suficiente para que o estruturador adote uma interpretação sem inferência indevida.

Isso precisa entrar no prompt.

Também inclua:

> Em C0, o agente deve usar apenas o texto do requisito como evidência. Uma ambiguidade em C0 pode ser resolvível se o próprio requisito fornecer evidência suficiente.
> Em C1 ou C2, o agente pode usar o contexto controlado, mas apenas quando ele trouxer evidência diretamente relacionada à ambiguidade.

---

## 6. Saída esperada do agente

A saída deve avaliar cada ambiguidade individualmente e gerar um status geral da execução.

```yaml
contextual_resolubility_validation:
  execution_id: "REQ-XX-CX"
  requirement_id: "REQ-XX"
  context_condition: "C0 | C1 | C2"

  has_ambiguity: true
  validation_summary: ""

  ambiguity_resolubility:
    - ambiguity_id: "AMB-01"
      fragment: ""
      ambiguity_type: ""

      resolubility_status: "resolvable | unresolved | not_applicable"

      supported_interpretation: null
      unsupported_interpretations:
        - ""

      evidence_from_requirement:
        - ""

      evidence_from_context:
        - ""

      missing_information:
        - ""

      justification: ""

      allowed_structuring_action: "use_supported_interpretation | flag_for_human_clarification | no_action_needed"

  overall_resolubility:
    status: "fully_resolvable | unresolved | no_ambiguity"
    explanation: ""
```

---

## 7. Como preencher os campos

### `supported_interpretation`

Preencher apenas quando houver evidência suficiente. Em `unresolved`, manter `null`.

### `unsupported_interpretations`

Listar interpretações possíveis que não têm sustentação suficiente.

### `evidence_from_requirement`

Deve conter apenas evidências presentes no requisito.

### `evidence_from_context`

Deve conter apenas evidências presentes no contexto controlado.

Em C0:

```yaml
evidence_from_context: []
```

### `missing_information`

Obrigatório quando o status for `unresolved`.

### `allowed_structuring_action`

Este é o principal campo para a orquestração.

Mapeamento recomendado:

```yaml
resolvable: "use_supported_interpretation"
unresolved: "flag_for_human_clarification"
not_applicable: "no_action_needed"
```

Mas a orquestração pode ignorar o Agente 3 quando o status geral for `unresolved`.

---

## 8. Status geral da execução

O status geral deve considerar todas as ambiguidades.

Regras:

```text
Se não há ambiguidades:
  overall_resolubility.status = no_ambiguity

Se todas as ambiguidades são resolvable:
  overall_resolubility.status = fully_resolvable

Se há pelo menos uma unresolved:
  overall_resolubility.status = unresolved
```

Importante: `unresolved` significa que o Agente 3 não deve ser chamado. A execução segue para a rota alternativa de formatação/revisão.

---

## 9. Prompt conceitual do Agente 2

```text
You are a contextual resolubility validation agent specialized in natural language requirements.

Your task is to evaluate the ambiguities detected in the requirement and determine whether each ambiguity provides enough evidence for the next step in the pipeline to adopt an interpretation safely during final requirement structuring or whether the execution must take the alternative formatting/review route.

Contextual resolubility does not mean that the system can produce any output. It means that there is enough evidence in the requirement text and/or in the controlled context to adopt an interpretation without unsupported inference.

Evaluate each ambiguity independently, while considering the full requirement and all detected ambiguities together.

Classify each ambiguity as:

- resolvable: there is enough evidence in the requirement or controlled context to support a specific interpretation;
- unresolved: the available evidence is not sufficient to eliminate the ambiguity safely, even if part of the requirement could still be described;
- not_applicable: there is no relevant ambiguity to validate.

Do not rewrite the requirement.
Do not produce the final structured requirement.
Do not invent missing information.
Do not use external knowledge.
Do not choose an interpretation based on plausibility alone.
Do not assume that C0 is always blocking.
Do not assume that C2 is always resolvable.

In C0, use only the requirement text as evidence.
In C1 or C2, use the controlled context only when it provides evidence directly related to the ambiguity.

For each ambiguity, provide:
- resolubility status;
- supported interpretation, if any;
- unsupported interpretations;
- evidence from the requirement;
- evidence from the context;
- missing information;
- justification;
- allowed structuring action for the next step in the pipeline.

Return the output in the required structured format.
```

---

## 10. Exemplo de decisão

### Caso unresolved em C0

```yaml
ambiguity_id: "AMB-01"
fragment: "If it is invalid"
ambiguity_type: "referential"
resolubility_status: "unresolved"
supported_interpretation: null
unsupported_interpretations:
  - "The access card is invalid."
  - "The PIN is invalid."
evidence_from_requirement:
  - "Both the access card and the PIN are mentioned before the pronoun 'it'."
evidence_from_context: []
missing_information:
  - "Which entity is considered invalid."
justification: "The requirement contains two possible antecedents for 'it', and no available evidence selects one safely."
allowed_structuring_action: "flag_for_human_clarification"
```

### Caso resolvible em C2

```yaml
ambiguity_id: "AMB-01"
fragment: "If it is invalid"
ambiguity_type: "referential"
resolubility_status: "resolvable"
supported_interpretation: "The PIN is invalid."
unsupported_interpretations:
  - "The access card is invalid."
evidence_from_requirement:
  - "Both the access card and the PIN are mentioned before the pronoun 'it'."
evidence_from_context:
  - "The business rule states that access must be denied when the entered PIN is invalid."
missing_information: []
justification: "The controlled context explicitly identifies the PIN as the invalid entity relevant to access denial."
allowed_structuring_action: "use_supported_interpretation"
```

## Decisão final

O Agente 2 deve ser definido como um **validador de segurança interpretativa**.

Ele não resolve, não estrutura e não reescreve.
Ele apenas responde:

> O próximo passo pode adotar uma interpretação com base nas evidências disponíveis?
