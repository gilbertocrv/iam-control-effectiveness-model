# kpi-kri-layer.md

> Camada de indicadores executivos do IAM Control Effectiveness Model.
> Não cria métricas novas. Reorganiza os dados já ingeridos em duas leituras complementares para audiências distintas.

---

## Objetivo

O modelo já produz scores técnicos por controle ISO e achados de risco com mapeamento LGPD. Esta camada acrescenta uma leitura executiva sobre os mesmos dados — sem alterar o pipeline, sem exigir campos adicionais.

A distinção entre KPI e KRI não é semântica. É funcional: eles respondem perguntas diferentes e disparam respostas diferentes.

---

## KPI vs KRI — a diferença que importa na prática

| | KPI | KRI |
|---|---|---|
| **Pergunta** | O controle está sendo executado? | O risco está aumentando? |
| **Audiência primária** | Gestor de IAM / CISO operacional | CISO / Board / Auditoria |
| **Sinal de alerta** | Processo degradando | Exposição acumulando |
| **Resposta esperada** | Ajuste de processo / capacidade | Decisão de remediação / escalada |
| **Exemplos** | Reviews concluídas, prazo de resolução | Conflitos críticos, cobertura MFA |

**Atenção:** KPI alto com KRI alto não é sinal de controle efetivo — é sinal de processo funcionando sobre risco não tratado. Esse padrão é o mais perigoso porque cria falsa sensação de controle. O modelo apresenta os dois painéis lado a lado exatamente para tornar essa tensão visível.

---

## KPIs do modelo

### `reviews_completed_pct`
Percentual de revisões de acesso concluídas no ciclo em relação ao total esperado.

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≥ 90% | 75–89% | < 75% |

Abaixo de 90% indica que um volume relevante de acessos passou pelo período sem revisão formal. Abaixo de 75%, o ciclo está comprometido — achados gerados a partir desse ciclo têm validade operacional reduzida.

---

### `avg_resolution_days`
Tempo médio em dias entre a identificação de um conflito de SoD e o registro de decisão pelo analista.

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≤ 15 dias | 16–30 dias | > 30 dias |

Esse indicador mede velocidade de resposta, não qualidade. Um tempo baixo com `untreated_pct` alto indica que as decisões estão sendo registradas rapidamente mas com resultado "aceitar risco" ou "monitorar" — o que exige justificativa explícita.

---

### `decisions_with_evidence_pct`
Percentual de decisões de risco que possuem evidência rastreável vinculada (hash SHA-1 de origem).

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≥ 90% | 75–89% | < 75% |

Decisões sem evidência são inauditáveis. Em contexto de LGPD ou ISO 27001, a ausência de rastreabilidade na decisão é tão problemática quanto a ausência da decisão em si.

---

### `exceptions_documented_pct`
Percentual de exceções ao controle que possuem justificativa formal registrada no ciclo.

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≥ 90% | 75–89% | < 75% |

Exceções não documentadas são riscos aceitos sem registro — o pior cenário em auditoria. Um número baixo aqui indica ou que o processo de exceção não existe formalmente ou que está sendo sistematicamente ignorado.

---

## KRIs do modelo

### `conflicts_critical`
Número absoluto de conflitos de SoD classificados como críticos no ciclo atual.

| Verde | Amarelo | Vermelho |
|---|---|---|
| 0 | 1–5 | > 5 |

Este é o indicador de maior peso para escalada executiva. Qualquer valor acima de 0 requer justificativa explícita — zero não é a meta apenas porque é arrumado, é a meta porque cada conflito crítico representa uma combinação de permissões que, se explorada, permite fraude, acesso indevido a dados sensíveis ou contorno de controles financeiros.

---

### `untreated_pct`
Percentual de conflitos críticos sem decisão de tratamento registrada.

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≤ 10% | 11–30% | > 30% |

Diferente de `conflicts_critical`, este indicador mede não o tamanho do problema mas a velocidade de resposta a ele. Um `untreated_pct` alto com `conflicts_critical` alto é o sinal que ativa a estimativa de exposição financeira (camada FAIR-inspired).

---

### `mfa_coverage_pct`
Percentual de contas privilegiadas com MFA ativo e verificado no ciclo.

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≥ 95% | 85–94% | < 85% |

O threshold é deliberadamente conservador: contas privilegiadas sem MFA são o vetor de comprometimento mais documentado em incidentes de acesso indevido. Abaixo de 85%, o risco é imediato e não mitigável por outros controles.

---

### `inactive_accounts_pct`
Percentual de contas ativas no sistema sem atividade registrada no período de avaliação.

| Verde | Amarelo | Vermelho |
|---|---|---|
| ≤ 5% | 6–10% | > 10% |

Contas inativas são superfície de ataque silenciosa — credenciais válidas sem dono ativo, frequentemente fora do processo de revisão. O threshold de 5% admite margem para contas de sistema e contas em processo de offboarding. Acima de 10%, o processo de provisionamento/desprovisionamento tem falha estrutural.

---

## Como usar os indicadores corretamente

### Para o gestor de IAM
Os KPIs mostram onde o processo precisa de capacidade ou ajuste. Um `reviews_completed_pct` em amarelo não é necessariamente sinal de negligência — pode ser sinal de volume crescente sem aumento de equipe. A conversa é de recursos, não de risco.

### Para o CISO
A combinação de KPI + KRI conta a história completa. O relatório executivo deve sempre apresentar os dois juntos, com a leitura da tensão entre eles: "o processo está funcionando a X%, mas o risco residual de SoD permanece em Y conflitos críticos sem tratamento."

### Para auditoria e board
Os KRIs são os números que importam. `conflicts_critical > 0` com `untreated_pct > 30%` é o sinal de que existe risco identificado, documentado e não tratado — exatamente o que auditoria interna e externa buscam. O modelo gera esse achado com rastreabilidade completa, o que transforma um potencial problema de conformidade em evidência de governança ativa.

---

## Thresholds são pontos de partida, não valores absolutos

Os thresholds desta documentação refletem práticas conservadoras de mercado para ambientes com controles ISO 27001 implementados. Organizações em setores regulados (financeiro, saúde, infraestrutura crítica) devem considerar thresholds mais restritivos. Organizações em estágios iniciais de maturidade podem precisar calibrar os thresholds para refletir sua baseline real antes de usar verde/amarelo/vermelho como sinal de desempenho.

O que não deve ser calibrado para baixo sem justificativa formal: `mfa_coverage_pct` e `conflicts_critical`. Esses dois indicadores têm relação direta com vetores de ataque documentados e com artigos LGPD de responsabilidade objetiva.
