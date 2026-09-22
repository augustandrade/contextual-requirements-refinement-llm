# Protocolo de avaliação

<!-- Posicionamento: subtópico da seção Metodologia, após a descrição do corpus e dos modelos.
     As RQs já foram apresentadas na Introdução; não reapresentá-las aqui. -->

A avaliação quantitativa consistiu em comparar, para cada execução, os campos extraídos da saída do "pipeline" com um gabarito derivado do corpus. Esse processo foi conduzido integralmente pelo script `evaluate.py`, que percorreu os arquivos `final_output.json` sem intervenção humana na classificação dos resultados. O gabarito de detecção foi determinado pelo campo `category_id`: requisitos de Cat-01 a Cat-04 são positivos — ambiguidade esperada —, e Cat-05 constituiu o único grupo de controle negativo. Derivar o gabarito diretamente do identificador de categoria evitou o uso de `taxonomy_accepted_types` como substituto — campo ausente em Cat-01, o que causaria sua classificação incorreta como controle.

A avaliação foi organizada em quatro blocos, correspondentes às três perguntas de pesquisa e a uma verificação complementar de integridade.

O **Bloco 1** mediu a detecção de ambiguidade pelo Agente 1, respondendo a RQ2. Por ser a etapa "context-free" do "pipeline", utilizou exclusivamente as execuções em C0, totalizando 15 instâncias por modelo. Cada instância foi classificada em verdadeiro positivo [TP], falso positivo [FP], falso negativo [FN] ou verdadeiro negativo [TN], e a partir desses contadores foram calculados precisão, revocação, F1 e especificidade.

O **Bloco 2** rastreou a rota do "pipeline" (`structured` ou `signaling`) ao longo das quatro condições de contexto, respondendo a RQ1. A métrica central foi ΔRoute(C2 − C0), que indicou se o contexto específico relevante converteu a rota; ΔRoute(C3 − C0) e Δ(C2 − C3) isolaram, respectivamente, o efeito do contexto irrelevante e o ganho puro de relevância com especificidade constante. Os ganhos por etapa — C0→C1 e C1→C2 — complementaram a análise. Esse bloco é descritivo: não existiu gabarito de rota esperada por condição.

O **Bloco 3** respondeu a RQ3: verificou se o tipo de ambiguidade detectado pelo Agente 1 coincidiu com os tipos aceitos declarados no corpus, tendo como referência a taxonomia de Pohl (2025) — cujas definições estão apresentadas na subseção Taxonomia de Ambiguidades. A avaliação restringiu-se a Cat-02, Cat-03 e Cat-04, categorias que possuem `taxonomy_accepted_types` preenchido, usando a execução em C0. O critério de acerto exigiu que ao menos um dos tipos detectados estivesse entre os aceitos, reconhecendo que o corpus admite conjuntos alternativos para requisitos em que mais de um tipo é defensável.

O **Bloco 4** foi uma verificação complementar de integridade estrutural da saída do pipeline, independente das perguntas de pesquisa: avaliou se o "pipeline" produziu um artefato utilizável em todas as condições. Para a rota `structured`, exigiu-se ao menos um item em `structured_requirements` com `final_statement` não vazio; para `signaling`, ao menos um item em `ambiguity_resolubility` com "status" `unresolved` ou equivalente. Saídas com rota desconhecida receberam valor nulo e foram excluídas do denominador da pontuação. Os resultados desse bloco foram retomados na análise de modos de falha, na seção de Resultados e Discussão.

## Análise estatística

O planejamento da análise estatística foi realizado antes da execução do experimento (Gil, 2018), com nível de significância α = 0,05 adotado como referência para todos os testes inferenciais.

Para RQ1, a comparação de rotas entre C2 e C3 foi conduzida de forma primariamente descritiva, por proporção de conversões `signaling→structured` por modelo. O teste de McNemar foi aplicado de forma exploratória quando o número de pares discordantes por modelo permitia interpretação (N ≥ 5); em razão do tamanho amostral reduzido (15 requisitos por modelo), os resultados foram reportados com a ressalva de baixo poder estatístico.

Para RQ2, os intervalos de confiança de 95% para precisão, revocação, F1 e especificidade foram estimados por bootstrap com 10.000 reamostras, calculados separadamente para cada modelo sobre as 15 execuções em C0. Esse método foi adotado por não pressupor distribuição normal e por ser adequado a amostras pequenas (Efron e Hastie, 2016).

Para RQ3, a comparação de acerto de tipo entre categorias foi reportada por proporção de acerto (acertos/3 por categoria por modelo), sem teste inferencial formal, dado que cada categoria continha apenas três requisitos — número insuficiente para qualquer teste de associação com poder estatístico interpretável. Os resultados foram apresentados em tabela de frequências cruzando categoria, modelo e condição C0.
