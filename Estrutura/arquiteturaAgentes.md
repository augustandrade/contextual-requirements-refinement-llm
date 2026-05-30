Sim. Agora faz sentido fechar a **arquitetura do sistema de agentes**, porque ela será a base dos prompts, do schema de saída e da implementação.

A arquitetura deve ser descrita como:

> **pipeline orquestrado com agentes funcionais baseados em LLMs**

Isso evita prometer autonomia excessiva e mantém coerência com sua metodologia.

---

# 1. Visão geral da arquitetura

O sistema será organizado como um pipeline sequencial, no qual cada agente funcional executa uma etapa específica do refinamento textual.

```text
Entrada
  ↓
Agente 1 — ambiguity_detector
  ↓
Agente 2 — contextual_resolubility_validator
  ↓
Agente 3 — requirement_structurer
  ↓
Agente 4 — output_consolidator
  ↓
Saída estruturada
```

A entrada de cada execução será:

```text
requisito textual + condição de contexto
```

A condição de contexto poderá ser:

* C0 — sem contexto;
* C1 — contexto geral;
* C2 — contexto resolutivo.

---

# 2. Princípio central da arquitetura

A arquitetura não deve ser apresentada como um conjunto de agentes autônomos conversando livremente.

Ela deve ser apresentada como um conjunto de agentes funcionais especializados, orquestrados em sequência, com entradas e saídas padronizadas.

O objetivo não é estudar comportamento emergente de agentes, mas usar agentes como mecanismo de divisão controlada da tarefa, mantendo a estruturação final do requisito como núcleo do sistema.

---

# 3. Agente 1 — Detector de Ambiguidades

## Função

Identificar trechos ambíguos ou problemáticos no requisito original.

## Entrada

* requisito textual;
* condição de contexto;
* contexto disponível, quando houver.

## Saída

* lista de ambiguidades;
* fragmento textual problemático;
* tipo de ambiguidade;
* possíveis interpretações;
* justificativa.

## Tipos de ambiguidade

Sugestão:

```text
lexical
syntactic
semantic
referential
logical
pragmatic_contextual
```

## Responsabilidade

Esse agente **não deve resolver** a ambiguidade.
Ele apenas identifica e descreve.

---

# 4. Agente 2 — Validador de Resolubilidade Contextual

## Função

Decidir se cada ambiguidade identificada pode ser resolvida com base no requisito e no contexto disponível.

## Entrada

* requisito original;
* contexto C0, C1 ou C2;
* ambiguidades identificadas pelo Agente 1;
* interpretações possíveis.

## Saída

Para cada ambiguidade:

```text
resolúvel
parcialmente resolúvel
bloqueante
não aplicável
```

Além disso:

* evidência encontrada no requisito;
* evidência encontrada no contexto;
* informação ausente;
* recomendação: resolver, sinalizar ou preservar.

## Regra principal

A ambiguidade só pode ser considerada resolúvel se houver evidência suficiente no requisito ou no contexto.

Caso contrário, deve ser classificada como bloqueante ou parcialmente resolúvel.

---

# 5. Agente 3 — requirement_structurer

## Função

Produzir a estrutura final do requisito, refinando a redação e organizando o artefato final.

## Entrada

* requisito original;
* análise de ambiguidades;
* análise de resolubilidade;
* contexto disponível;
* metadados identificados pelo agente anterior.

## Saída

Um artefato estruturado com requisito refinado, tipo do requisito e observações de estruturação.

## Responsabilidade

O requirement_structurer pode executar, quando necessário, operações auxiliares de concern separation e decomposition como parte da estruturação final.

Essas operações só devem ser acionadas quando o requisito misturar funcionalidade, qualidade, restrição ou múltiplas ações independentes.

O agente não deve criar novas informações, não deve resolver ambiguidades bloqueantes e não deve degradar requisitos já bem estruturados.

## Estrutura de saída sugerida

```yaml
id:
type: functional_requirement | quality_requirement | constraint | mixed_requirement
source_fragment:
refined_text:
structuring_notes:
  concern_separation:
    applied: true | false
    notes: []
  decomposition:
    applied: true | false
    notes: []
structured_elements:
  - field: 
    value:
related_requirements:
final_statement:
```

---

# 6. Agente 4 — output_consolidator

## Função

Unificar as saídas intermediárias em um único resultado final padronizado.

## Entrada

* saídas dos agentes anteriores.

## Saída final

Um objeto estruturado contendo:

```yaml
execution_id:
requirement_id:
context_condition:
input_requirement:
context_used:

ambiguity_analysis:
contextual_resolubility_analysis:
requirement_structuring:
final_assessment_notes:
```

Esse agente também deve organizar:

* ambiguidades resolvidas;
* ambiguidades bloqueantes;
* requisitos finais;
* requisitos preservados;
* limitações.

---

# 7. Fluxo decisório principal

A arquitetura precisa ter uma regra clara para bloqueios:

```text
Se a ambiguidade for resolúvel:
    segue para refinamento e estruturação.

Se for parcialmente resolúvel:
    refina apenas as partes sustentadas e sinaliza pendências.

Se for bloqueante:
    não força reescrita da parte ambígua.
    registra o problema, a informação ausente e a pergunta sugerida.

Se não houver problema relevante:
    preserva ou realiza ajuste formal mínimo.
```

Essa regra é central para o seu TCC.

---

# 8. Onde entra o checklist

O checklist **não entra dentro do pipeline de geração**.

Ele entra depois, na etapa de avaliação.

Fluxo completo:

```text
Corpus + contexto
  ↓
Pipeline de agentes
  ↓
Saída estruturada
  ↓
Checklist de avaliação
  ↓
Classificação qualitativa
```

Você até pode implementar um avaliador automático depois, mas, metodologicamente, a avaliação principal deve ser qualitativa.

---

# 9. Arquitetura mínima recomendada para desenvolvimento

Para o primeiro protótipo, eu implementaria assim:

```text
1. load_requirement()
2. build_execution_input()
3. run_ambiguity_detector()
4. run_resolubility_validator()
5. run_requirement_structurer()
6. run_output_consolidator()
7. save_output()
```

Cada etapa salva um arquivo intermediário.

Exemplo:

```text
/outputs/REQ-01/C0/
  01_input.json
  02_ambiguity_detection.json
  03_resolubility_validation.json
  04_requirement_structuring.json
  05_final_output.json
```

Isso ajuda muito na rastreabilidade.

---

# 10. Texto metodológico para inserir no TCC

Você pode descrever a arquitetura assim:

> O sistema foi projetado como um pipeline orquestrado com agentes funcionais baseados em LLMs. Cada agente foi responsável por uma etapa específica do refinamento textual, recebendo como entrada a saída produzida pela etapa anterior e gerando registros intermediários para posterior análise. A arquitetura foi organizada em quatro agentes principais: detector de ambiguidades, validador de resolubilidade contextual, estruturador de requisitos e consolidador da saída. As operações de separação de concerns e decomposição não foram tratadas como etapas independentes, mas como recursos auxiliares acionados dentro da estruturação final quando necessários para produzir um requisito estruturado adequado.

---

# 11. Decisão recomendada

Eu fecharia a arquitetura com estes 4 agentes:

1. Detector de Ambiguidades
2. Validador de Resolubilidade Contextual
3. Estruturador de Requisitos
4. Consolidador da Saída

Essa arquitetura é clara, alinhada com o pipeline reduzido, avaliável e viável para implementar.
