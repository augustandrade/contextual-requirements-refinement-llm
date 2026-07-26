# Gulli — Agentic Design Patterns: Appendix A
## Advanced Prompting Techniques (referência para avaliação de prompts)

> Fonte: Gulli, A. *Agentic Design Patterns*. Appendix A: Advanced Prompting Techniques.
> Este documento é uma síntese estruturada para reutilização na avaliação de prompts do pipeline TCC.

---

## 1. Core Prompting Principles

| Princípio | Definição | Checklist de avaliação |
|---|---|---|
| **Clarity & Specificity** | Instruções não ambíguas e precisas. Definir tarefa, formato de saída e restrições relevantes. | O prompt define claramente o que fazer, o que retornar e os limites da tarefa? |
| **Conciseness** | Linguagem direta, sem verborragia. Estruturas complexas confundem o modelo. | Há wording desnecessário, seções redundantes ou exemplos prolixos? |
| **Using Verbs** | Verbos de ação ativam padrões de treinamento relevantes. Preferir: *Classify, Identify, Determine, Explain, Return, Extract, Evaluate, List.* | O prompt usa verbos de ação imperativa, não frases nominais ou passivas? |
| **Instructions Over Constraints** | Instruções positivas > restrições negativas. DO NOT em excesso faz o modelo focar em evitação, não em objetivos. Exceção: constraints são válidos para segurança ou formatting estrito. | Há DO NOTs que podem ser reformulados positivamente? Restrições restantes são definitórias (escopo) ou comportamentais? |
| **Experimentation & Iteration** | Meta-princípio: prompt engineering é iterativo. Documentar versões, testar, analisar shortcomings, refinar. | n/a para avaliação de prompt individual |

---

## 2. Basic Prompting Techniques

### 2.1 Zero-Shot Prompting
- Sem exemplos. O modelo usa apenas pré-treinamento.
- **Quando usar**: tarefas simples, bem representadas no treino (QA básico, completação, sumarização genérica).
- **Risco**: inconsistência de formato em tarefas especializadas.

### 2.2 One-Shot Prompting
- Um exemplo input→output antes da tarefa.
- **Quando usar**: formato específico ou menos comum; uma instância ancorando o padrão.

### 2.3 Few-Shot Prompting
- 3–5 exemplos input→output (regra geral; pode escalar para many-shot com contextos longos).
- **Quando usar**: tarefas de classificação, extração com schema, formatação específica, onde zero/one-shot não produzem resultados consistentes.
- **Critérios de qualidade dos exemplos**:
  - **Accuracy**: exemplos corretos — um erro pode propagar padrão errado.
  - **Diversity**: cobrir variações e edge cases que o modelo encontrará.
  - **Representative**: cobrir todas as classes/subtipos relevantes.
  - **Class mixing**: para classificação, intercalar exemplos de classes diferentes (evita overfitting à sequência).
- **Checklist few-shot**:
  - Pelo menos 3 exemplos?
  - Todas as classes/subtipos cobertos?
  - Exemplos de classes intercalados (não todos juntos)?
  - Nenhum exemplo usa texto verbatim do corpus de avaliação (risco de data leakage)?

---

## 3. Structuring Prompts

### 3.1 System Prompting
- Define o contexto global, persona, tom e regras operacionais do modelo para toda a sessão.
- Influencia estilo, escopo e approach de todas as respostas.
- **Checklist**: O system prompt define claramente o papel, o domínio e as regras de comportamento sem conteúdo que nunca chegará ao modelo (seções de documentação, snippets de chamada, etc.)?

### 3.2 Role Prompting
- Atribui persona/identidade ao modelo: expertise, estilo, ponto de vista.
- Ex.: "You are an Expert Requirements Engineering Quality Agent…"
- **Checklist**: A persona é específica ao domínio? Inclui referência teórica/metodológica relevante?

### 3.3 Using Delimiters
- Triplos backticks ` ``` `, tags XML (`<instruction>`, `<context>`), marcadores (`---`) separam visualmente seções de instrução, contexto e exemplos.
- Reduz ambiguidade sobre o papel de cada bloco de texto.
- **Checklist**: Exemplos usam delimitadores (blocos de código, YAML fenced)? Instruções e dados de entrada são visualmente distinguíveis?

### 3.4 Contextual Engineering
- Fornece dinamicamente informação de background relevante para a tarefa (RAG, histórico de conversa, tool outputs, dados implícitos).
- Camadas: system prompt (estático) + retrieved documents + tool outputs + implicit data.
- **Princípio**: a qualidade do output depende mais da riqueza do contexto fornecido do que da arquitetura do modelo.
- **Para agents de pipeline**: o contexto é o `base_requirement_text` (user content); system prompt é estático. Não mencionar no system prompt informações que o modelo nunca verá.

### 3.5 Structured Output
- Solicitar output em formato máquina-legível (JSON, YAML, CSV) com schema explícito.
- Força estrutura e reduz hallucinations em tarefas de extração/classificação.
- Fornecer o schema completo (campos, tipos, restrições) e um exemplo de output no próprio prompt.
- **Checklist**: Schema definido? Campos anotados? Output rules explícitas (o que fazer em cada caso)? Exemplo de output presente?

---

## 4. Reasoning and Thought Process Techniques

### 4.1 Chain of Thought (CoT)
- Instruir o modelo a externalizar raciocínio passo a passo antes da resposta final.
- **Zero-Shot CoT**: adicionar "think step by step" ou equivalente.
- **Few-Shot CoT**: exemplos incluem o raciocínio intermediário + resposta final.
- **Vantagens**: maior acurácia em dedução/cálculo; output interpretável; mais robusto a mudanças de versão do modelo.
- **Custo**: token usage maior.
- **Best practice**: resposta final *depois* do raciocínio (geração influencia próximo token).
- **Checklist**: O processing guidance exige que o modelo percorra etapas de raciocínio explícitas? O output externaliza o raciocínio (campo de explicação, reason, etc.) mesmo para o caso negativo?

### 4.2 Self-Consistency
- Gerar múltiplos caminhos de raciocínio (alta temperatura) e selecionar a resposta mais frequente (majority vote).
- **Quando usar**: tarefas com múltiplos caminhos válidos, alta sensibilidade a erros de um único attempt.
- **Custo**: múltiplas chamadas ao modelo.

### 4.3 Step-Back Prompting
- Primeiro perguntar ao modelo um princípio geral relacionado à tarefa; usar essa resposta como contexto para a pergunta específica.
- Ativa conhecimento de background e estratégias de raciocínio mais amplas.

### 4.4 Tree of Thoughts (ToT)
- Extensão do CoT: explorar múltiplos caminhos de raciocínio concorrentemente (estrutura de árvore).
- Nós = "thoughts" (sequências linguísticas coerentes como passo intermediário).
- Permite backtracking e avaliação de alternativas.
- **Quando usar**: problemas complexos que requerem exploração, avaliação de múltiplas possibilidades.

---

## 5. Action and Interaction Techniques

### 5.1 Tool Use / Function Calling
- O modelo gera output estruturado (JSON) especificando ferramenta e parâmetros; o sistema executa e retorna o resultado.
- O prompt deve descrever ferramentas disponíveis (nome, propósito, parâmetros).

### 5.2 ReAct (Reason & Act)
- Combina CoT com tool use em loop interleaved: **Thought → Action → Observation → Thought → …**
- Permite ao agente coletar informação dinamicamente e refinar o approach com base nos resultados.

---

## 6. Advanced Techniques

### 6.1 Automatic Prompt Engineering (APE)
- Usar o próprio LLM para gerar, avaliar e refinar prompts automaticamente.
- Requer goldset (exemplos de alta qualidade) e função objetivo (métrica de avaliação).
- Estratégias: few-shot example optimization + instructional prompt optimization.

### 6.2 Iterative Prompting / Refinement
- Começar com prompt simples, analisar outputs, identificar shortcomings, refinar.
- Processo human-driven (vs. APE que é automatizado).

### 6.3 Providing Negative Examples
- Mostrar ao modelo input + output *indesejado* (o que NÃO gerar).
- Uso cuidadoso: complementa "Instructions Over Constraints", não substitui.
- **Quando usar**: clarificar fronteiras ou prevenir tipos específicos de resposta incorreta.
- **Checklist**: Há casos negativos nos exemplos que explicitam o que não flagear/retornar?

### 6.4 Using Analogies
- Enquadrar a tarefa via analogia para facilitar a compreensão do papel ou do output esperado.
- Útil para tarefas criativas ou roles complexos.

### 6.5 Factored Cognition / Decomposition
- Decompor tarefa complexa em sub-tarefas; prompts separados para cada sub-tarefa; combinar resultados.
- Relacionado a prompt chaining e planning.
- **Checklist**: O processing guidance decompõe a decisão em etapas ordenadas?

### 6.6 Retrieval Augmented Generation (RAG)
- Recuperar documentos/dados externos e incluir no prompt como contexto.
- Mitiga hallucination e fornece acesso a conhecimento pós-treinamento ou proprietário.

### 6.7 Persona Pattern (User Persona)
- Descrever o *usuário/audiência* do output (não a persona do modelo).
- Calibra linguagem, complexidade e tipo de informação fornecida.

---

## 7. Checklist consolidado para avaliação de prompt de agente

Use esta lista ao avaliar qualquer prompt do pipeline:

### Princípios gerais
- [ ] Tarefa, formato de saída e limites de escopo claramente definidos (Clarity & Specificity)
- [ ] Sem wording desnecessário, seções não consumidas pelo modelo, ou informações que o modelo nunca verá (Conciseness)
- [ ] Verbos de ação imperativa (Verbs)
- [ ] Instruções positivas; DO NOTs apenas para segurança ou fronteiras definitórias (Instructions Over Constraints)

### Persona e contexto
- [ ] Role prompting específico ao domínio com referência metodológica (Role Prompting)
- [ ] System prompt não contém seções de documentação operacional nem referências cross-agent desnecessárias (Contextual Engineering)

### Formato de saída
- [ ] Schema de output definido com campos anotados (Structured Output)
- [ ] Output rules explícitas para cada caso (verdadeiro, falso, borda)
- [ ] Campos de raciocínio externalizados para TODOS os casos — inclusive o caso negativo (CoT)

### Exemplos
- [ ] Mínimo 3 exemplos cobrindo todas as classes/subtipos (Few-Shot)
- [ ] Classes intercaladas, não todas consecutivas (Class Mixing)
- [ ] Casos negativos presentes mostrando o que não flagear (Negative Examples)
- [ ] Nenhum exemplo usa texto verbatim do corpus de avaliação (No Data Leakage)
- [ ] Exemplos com delimitadores claros input/output (Delimiters)

### Raciocínio
- [ ] Processing guidance decompõe a decisão em etapas ordenadas (Factored Cognition / CoT)
- [ ] Campo de explicação/reason preenchido tanto no caso verdadeiro quanto no falso (CoT Transparency)
