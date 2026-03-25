# fair-financial-impact.md

> Camada opcional conectada ao IAM Control Effectiveness Model.
> Não cria novo pipeline de entrada. Reutiliza métricas já ingeridas pelo dashboard para estimar a exposição financeira anual associada a conflitos de SoD não tratados.

---

## Objetivo

Traduzir o achado operacional de SoD em linguagem financeira — sem substituir o modelo de controles e sem exigir novos dados de entrada.

A pergunta que esta camada responde é precisa: **dado o volume de conflitos críticos ativos hoje, qual é a exposição financeira anual estimada se nenhum tratamento for aplicado?**

---

## O que vem dos dados e o que é premissa do analista

Esta distinção é essencial antes de apresentar qualquer número a uma audiência executiva.

| Parâmetro | Fonte | Observação |
|---|---|---|
| `conflicts_critical` | Dados ingeridos (SoD) | Valor real do ciclo atual |
| `untreated_pct` | Dados ingeridos (SoD) | Percentual real sem tratamento registrado |
| Magnitude por evento | **Premissa do analista** | Não vem dos dados — deve ser calibrada |
| Intervalo entre eventos | **Premissa do analista** | Não vem dos dados — deve ser calibrada |
| Redução com tratamento | **Premissa do analista** | Não vem dos dados — deve ser calibrada |
| Custo de controle | **Premissa do analista** | Não vem dos dados — deve ser calibrada |

**Os dois primeiros parâmetros são evidência. Os quatro últimos são hipóteses de trabalho.** O número final só é tão confiável quanto essas hipóteses.

---

## Lógica aplicada

```text
conflitos_ativos      = conflicts_critical × (untreated_pct / 100)
frequência_anual      = conflitos_ativos × (12 / meses_entre_eventos)
exposição_anual       = frequência_anual × magnitude_por_evento
exposição_residual    = exposição_anual × (1 − redução_com_tratamento)
valor_da_redução      = exposição_anual − exposição_residual
ROI_do_controle       = (valor_da_redução − custo_de_controle) / custo_de_controle
```

A lógica é inspirada no FAIR (Factor Analysis of Information Risk), mas aplicada como **aproximação determinística** — não probabilística. O FAIR completo trabalha com distribuições de probabilidade (Monte Carlo / PERT) sobre cada variável. Esta implementação usa valores pontuais para produzir estimativas rápidas de ordem de grandeza.

Isso significa: o resultado é adequado para **priorização e conversa executiva**. Não é adequado para orçamentos de seguro, provisões contábeis ou decisões de investimento sem análise adicional.

---

## Premissas padrão e como calibrá-las

### Magnitude por evento — R$ 80.000 (default)

Representa perda primária + custo de resposta a incidente em um evento de acesso indevido por conflito de SoD. É o parâmetro de maior impacto no resultado final.

**Como calibrar:**
- Histórico interno de incidentes com impacto financeiro documentado
- Benchmarks setoriais (ex: relatórios IBM Cost of a Data Breach, segmento Brasil)
- Estimativa conservadora: custo de investigação forense + notificação regulatória + horas de remediação

### Intervalo entre eventos — 24 meses (default)

Representa a frequência esperada de materialização de um evento de perda decorrente de um conflito de SoD ativo.

**Como calibrar:**
- Histórico de uso indevido de acesso privilegiado nos últimos 3–5 anos
- Frequência de achados de auditoria que resultaram em ação disciplinar ou investigação
- Para ambientes com alta rotatividade de função ou terceiros: considerar intervalos menores (12 meses)

### Redução com tratamento — 90% (default)

Representa a efetividade esperada do controle compensatório após tratamento dos conflitos.

**Como calibrar:**
- Baseado no tipo de controle aplicado: revisão e revogação de acesso tende a 95%+; alertas de monitoramento sem revogação tende a 50–70%
- Nunca usar 100% — controles compensatórios reduzem, não eliminam risco

### Custo de controle — R$ 20.000 (default)

Representa o custo direto do projeto de remediação dos conflitos identificados.

**Como calibrar:**
- Horas de analista × tarifa interna ou de consultoria
- Custo de ferramentas adicionais necessárias
- Custo de revalidação e documentação pós-remediação

---

## Exemplo completo

**Dados do ciclo:**
- `conflicts_critical = 12`
- `untreated_pct = 30%`

**Premissas usadas (defaults):**
- Magnitude: R$ 80.000
- Intervalo: 24 meses
- Redução: 90%
- Custo de controle: R$ 20.000

**Cálculo:**
- Conflitos ativos: 12 × 30% = **3,6**
- Frequência anual: 3,6 × (12/24) = **1,8 eventos/ano**
- Exposição anual: 1,8 × R$ 80.000 = **R$ 144.000**
- Exposição residual: R$ 144.000 × 10% = **R$ 14.400**
- Valor da redução: R$ 144.000 − R$ 14.400 = **R$ 129.600**
- ROI: (R$ 129.600 − R$ 20.000) / R$ 20.000 = **548%**

**Sinal sugerido:** TRATAR COM PRIORIDADE (exposição anual > R$ 100.000)

---

## Saída adicionada ao ciclo (JSON)

```json
{
  "fair_summary": {
    "connector_status": "CONNECTED",
    "source_metric": "5.3",
    "active_conflicts_est": 3.6,
    "loss_event_frequency_annual": 1.8,
    "loss_magnitude": 80000,
    "annual_exposure": 144000,
    "residual_exposure": 14400,
    "risk_reduction_value": 129600,
    "control_cost": 20000,
    "control_roi_pct": 548,
    "decision_hint": "TRATAR COM PRIORIDADE"
  }
}
```

O campo `connector_status` retorna `NOT_APPLICABLE` quando `conflicts_critical = 0` — evitando que o painel apareça em ciclos sem conflitos críticos ativos.

---

## Limites desta implementação

**O que esta camada faz bem:**
- Produz estimativa de ordem de grandeza em segundos, a partir de dados já disponíveis
- Torna o risco operacional comparável com outras decisões de investimento
- Gera ROI documentável para justificar priorização de remediação

**O que esta camada não faz:**
- Não modela incerteza — usa valores pontuais, não distribuições
- Não considera correlação entre conflitos — trata cada conflito como evento independente
- Não captura perdas secundárias (reputação, litígios, impacto regulatório de longo prazo)
- Não substitui uma análise FAIR completa para decisões de alocação de orçamento de segurança acima de R$ 500.000

---

## Referência

Open FAIR Body of Knowledge — The Open Group  
[https://www.opengroup.org/open-fair](https://www.opengroup.org/open-fair)
