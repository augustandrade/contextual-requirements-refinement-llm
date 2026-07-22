# Apêndice A — Checklist de Avaliação Qualitativa dos Outputs do Agente 3

Este checklist é aplicado aos outputs do Agente 3 (Estruturador) para avaliar a adequação qualitativa dos requisitos estruturados produzidos. É composto por três itens — um por dimensão qualitativa — respondidos com **Sim**, **Não** ou **N/A**.

**Escopo de aplicação:** instâncias com rota `structured` (Agent 3 invocado). Aplicado sobre uma amostra representativa de um modelo por condição de contexto (C0, C1, C2) para cada um dos 14 requisitos do corpus. O objetivo é cruzar com o resultado quantitativo de D4 para verificar se completude estrutural implica adequação semântica.

---

## Q1 — O output preserva o significado original sem omissões ou adições?

**Fundamento:** Pohl (2025) define que um requisito de qualidade deve ser *completo* — contendo todas as informações necessárias para sua implementação e verificação — e *preciso* — sem ambiguidade de interpretação introduzida pelo próprio documento. Um requisito estruturado que omite condições do original ou introduz especificações novas viola ambos os critérios simultaneamente.

**Como responder:**

1. Identifique no texto-base todos os elementos semânticos obrigatórios: **sujeito** (quem ou o quê realiza), **ação** (o que é feito), **objeto** (sobre o quê), e **qualificadores** (condições temporais, quantitativas ou de escopo).
2. Verifique se cada um desses elementos está presente no output do Agente 3 com equivalência de sentido — não necessariamente com as mesmas palavras, mas sem alteração de significado.
3. Verifique se o output não acrescentou nenhum elemento ausente no texto-base **e** no contexto fornecido na condição vigente.

**Responda Sim** se todos os elementos do texto-base estão presentes no output e nenhum elemento novo foi introduzido.

**Responda Não** se ao menos um elemento foi omitido, alterado em sentido, ou acrescentado sem suporte no texto-base ou contexto.

**Responda N/A** apenas se o output está na rota `signaling` (Agente 3 não foi invocado) — fora do escopo deste checklist.

---

## Q2 — A classificação do tipo de requisito (e decomposição, se aplicável) está correta?

**Fundamento:** Pohl (2025) distingue três tipos de requisito de sistema: *requisito funcional* — descreve um serviço ou comportamento que o sistema deve executar; *requisito de qualidade* — especifica uma propriedade mensurável do sistema (desempenho, confiabilidade, segurança, usabilidade); e *restrição* — limita as opções de projeto, tecnologia ou processo sem descrever comportamento do sistema. Quando há "concern mixing", Pohl (2025) determina que os dois elementos devem ser separados em artefatos com ciclos de vida independentes: um requisito funcional e um requisito de qualidade.

**Como responder:**

**Caso sem concern mixing (`has_concern_mixing: false`):**

1. Leia o requisito estruturado e identifique seu conteúdo principal.
2. Aplique as definições de Pohl (2025):
   - Se o conteúdo principal descreve **o que o sistema faz** (ação sobre dados, entidades ou usuários) → deve ser `functional_requirement`.
   - Se o conteúdo principal descreve **como o sistema deve se comportar** em termos de propriedade mensurável (tempo, taxa, disponibilidade, segurança) → deve ser `quality_requirement`.
   - Se o conteúdo principal expressa **uma limitação imposta ao sistema** (tecnologia obrigatória, padrão regulatório, restrição orçamentária) → deve ser `constraint`.
3. Compare a classificação atribuída pelo Agente 3 com o tipo esperado.

**Caso com concern mixing (`has_concern_mixing: true`):**

1. Verifique se o output contém exatamente dois artefatos.
2. Para cada artefato, aplique as definições acima.
3. Verifique se o requisito funcional resultante **não contém** o critério de qualidade como parte de seu enunciado.
4. Verifique se o requisito de qualidade resultante **não repete** a ação funcional como conteúdo principal — deve expressar apenas o critério mensurável.
5. Verifique se cada artefato possui **sentido autônomo**: pode ser lido, rastreado e verificado independentemente do outro (critério de atomicidade, Pohl, 2025).

**Responda Sim** se a classificação está correta e, quando aplicável, a decomposição atende aos cinco critérios acima.

**Responda Não** se a classificação está incorreta ou se algum critério de decomposição não foi atendido.

**Responda N/A** se a instância está na rota `signaling`.

---

## Q3 — O output não introduz condições ausentes no texto e no contexto?

**Fundamento:** Pohl (2025) define que um requisito deve ser *verificável*: deve ser possível determinar objetivamente, por inspeção ou teste, se o sistema satisfaz o requisito. Um requisito que incorpora valores, limites ou premissas não declarados no texto-base nem no contexto fornecido torna-se inverificável em relação à especificação original — não há como confirmar se o valor introduzido é correto.

**Como responder:**

1. Liste todos os valores quantitativos, limites, prazos, condições de ativação e premissas de domínio presentes no output do Agente 3.
2. Para cada item listado, verifique se ele está presente em ao menos uma das seguintes fontes: (a) texto-base do requisito; (b) contexto controlado fornecido na condição vigente (C1: domínio e glossário; C2: domínio, glossário, regras de negócio e restrições).
3. Qualquer item sem suporte em nenhuma das fontes constitui uma inferência não suportada.

**Responda Sim** se todos os elementos do output têm suporte no texto-base ou no contexto fornecido.

**Responda Não** se ao menos um elemento foi introduzido sem suporte nas fontes disponíveis.

**Responda N/A** se a instância está na rota `signaling`, ou se o contexto da condição C0 não oferece base suficiente para avaliar o item 3 em requisitos de domínio (nesses casos, a ausência de contexto é a própria condição experimental — registrar como observação, não como erro).

---

## Pontuação e cruzamento com o quantitativo

O score qualitativo por instância é:

> **Score qualitativo = Sim / (Sim + Não)**

O cruzamento com D4 (avaliação quantitativa de completude estrutural) segue a matriz abaixo:

| D4 (quantitativo) | Q1 + Q2 + Q3 (qualitativo) | Interpretação |
|---|---|---|
| Correto | Todos Sim | Output completo e semanticamente adequado — pipeline funciona plenamente |
| Correto | Algum Não | D4 superestima qualidade: o output é estruturalmente completo mas semanticamente inadequado |
| Incorreto | — | Falha estrutural detectada pelo quantitativo; qualitativo não aplicável |

