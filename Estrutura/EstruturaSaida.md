## Formato de saída estruturada

O sistema produzirá, para cada requisito textual analisado, uma saída estruturada composta por quatro partes principais:

1. **Ambiguity analysis**
   Registra os trechos ambíguos, os tipos de ambiguidade, as interpretações possíveis e o grau de confiança da análise.

2. **Contextual resolubility analysis**
   Registra se cada ambiguidade é resolvable, partially_resolvable, blocking ou not_applicable, com base apenas no requisito e no contexto disponível.

3. **Requirement structuring**
   Registra o requisito refinado e estruturado. Quando necessário, este bloco também pode registrar operações auxiliares de concern separation e decomposition como parte da estruturação final, sem tratá-las como agentes independentes.

4. **Output consolidation**
   Reúne a saída final, preservando o histórico mínimo de decisões e observações necessárias para rastreabilidade.

## Estrutura sugerida

```yaml
execution_id:
requirement_id:
context_condition:
input_requirement:
context_used:

ambiguity_analysis:
  identified_issues: []
  ambiguity_types: []
  possible_interpretations: []

contextual_resolubility_analysis:
  overall_resolubility: "blocking | partially_resolvable | resolvable | not_applicable"
  issue_decisions: []

requirement_structuring:
  structured_requirement_type: "functional | quality | constraint | mixed"
  refined_text:
  auxiliary_operations:
    concern_separation:
      applied: true
      notes: []
    decomposition:
      applied: true
      notes: []

output_consolidation:
  final_artifact:
  preserved_elements: []
  unresolved_issues: []
  final_assessment_notes: []
```

## Regra de uso

Concern separation e decomposition continuam relevantes como aspectos avaliativos e operacionais, mas não aparecem como etapas independentes do pipeline. Elas só são ativadas dentro de requirement_structurer quando o requisito mistura funcionalidade, qualidade, restrição ou múltiplas ações independentes.

---

## Como isso afeta sua metodologia

Com essa definição, aquele checklist anterior fica parcialmente resolvido.

Você já definiu:

* formato final do requisito estruturado;
* separação por tipo de requisito;
* uso de template sintático para requisito funcional;
* campos principais do requisito;
* relação entre requisito funcional, qualidade e restrição.

Ainda falta definir:

* tamanho e origem do corpus;
* rubrica de avaliação qualitativa;
* referência manual/gabarito;
* configuração do LLM;
* como você vai representar os outputs no TCC: tabela, JSON, relatório textual ou ambos.

Minha recomendação: no TCC, use **tabelas padronizadas** para apresentar os resultados. JSON pode aparecer como apoio técnico ou apêndice, mas a banca provavelmente vai entender melhor uma tabela com campos estruturados e sentença final refinada.

