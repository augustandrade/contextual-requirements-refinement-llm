# Corpus controlado

Para assegurar reprodutibilidade, foi construído um corpus de 15 requisitos em linguagem natural extraídos da literatura, precedido por uma execução-piloto com seis requisitos construídos pelo autor, cujos resultados orientaram o ajuste dos "prompts" e a definição das categorias de defeito adotadas.

## Taxonomia de ambiguidades

A classificação das ambiguidades adotou a taxonomia de Pohl (2025), que distingue cinco tipos: **(1) lexical**, quando um termo admite múltiplos significados e o contexto não permite discriminar qual se aplica; **(2) sintática**, quando a estrutura gramatical da sentença admite mais de uma árvore de análise com interpretações distintas; **(3) semântica**, quando operadores lógicos ou relacionais — como "e", "ou", "se" — não delimitam com precisão as condições a que se aplicam; **(4) referencial**, quando um pronome, anáfora ou expressão nominal possui mais de um antecedente plausível; e **(5) vaguidade**, quando predicados, quantificadores ou termos de fronteira impedem a verificação objetiva do critério enunciado. Essa taxonomia foi adotada tanto na construção do gabarito do corpus quanto nos "prompts" do Agente 1, de modo que os tipos detectados pelo "pipeline" fossem comparáveis aos tipos aceitos declarados manualmente.

## Categorias do corpus

Os 15 requisitos foram distribuídos em cinco categorias: **(Cat-01) estrutural**, com requisitos que apresentavam defeitos de formação — não-factibilidade, não-atomicidade e incompletude —, referenciados na taxonomia de *requirement smells* de Veizaga et al. (2024) e nos critérios de qualidade de Pohl (2025); **(Cat-02) linguística**, com ambiguidades sintáticas, referenciais e lógicas independentes de conhecimento de domínio; **(Cat-03) de domínio**, com ambiguidades lexicais e semânticas cuja resolução dependia de conhecimento especializado ou de definições operacionais ausentes; **(Cat-04) de vaguidade**, com requisitos que empregavam quantificadores, termos de fronteira ou predicados temporais imprecisos (Pohl, 2025); e **(Cat-05) de controle**, com requisitos intencionalmente bem formados e sem defeitos esperados, para verificar a taxa de falsos positivos do "pipeline".

## Condições de contexto

Cada requisito foi avaliado sob quatro condições de contexto: C0 (sem contexto); C1 (domínio do sistema e glossário de termos periféricos, excluindo o fragmento ambíguo); C2 (acumula C1 e adiciona conteúdo que endereça diretamente o fragmento ambíguo, na forma de definição operacional, regra de negócio ou restrição); e C3 (acumula C1 e adiciona conteúdo específico sobre um aspecto diferente do requisito, nunca o fragmento ambíguo). O delineamento segue uma estrutura 2×2 que cruza especificidade e relevância do contexto injetado, de modo que a comparação C2 vs. C3 isola o efeito da relevância com especificidade constante. C0 é executado para todos os requisitos; C1, C2 e C3, apenas quando o Agente 1 detecta ambiguidade.

Com 15 textos-base e quatro condições, o corpus totaliza 60 instâncias experimentais. Executado sobre os sete modelos avaliados, o experimento compreende 420 execuções (60 instâncias × 7 modelos). A distinção entre texto-base — o requisito selecionado para o corpus — e instância experimental — a combinação entre requisito e condição de contexto — evita ambiguidade metodológica ao reportar os resultados. O corpus é descrito no Apêndice A e está disponível em Andrade (2026).

## Gabarito de avaliação

Para cada requisito, o corpus definiu o campo `taxonomy_accepted_types` — uma lista dos tipos de ambiguidade esperados, elaborada pelo autor segundo a taxonomia de Pohl (2025) e validada pelo professor orientador. Uma lista não-vazia indicou ambiguidade esperada e serviu de gabarito para a avaliação quantitativa; uma lista vazia caracterizou os requisitos do grupo de controle. O tipo de ambiguidade detectado pelo Agente 1 foi confrontado com os tipos declarados nessa lista no Bloco 3 do protocolo de avaliação.

## Idioma

Os requisitos foram mantidos no idioma original das fontes, predominantemente em inglês, para preservar os fenômenos linguísticos analisados — a tradução introduziria ou eliminaria ambiguidades não presentes no texto original. Estudos recentes indicaram que modelos multilíngues apresentaram forte influência do inglês tanto em seus espaços representacionais quanto na naturalidade de suas saídas em outros idiomas (Schut et al., 2025; Guo et al., 2025), e que tarefas traduzidas não capturaram adequadamente nuances do português brasileiro (Almeida et al., 2025). Como delimitação, os resultados deste estudo referiram-se a requisitos em inglês.
