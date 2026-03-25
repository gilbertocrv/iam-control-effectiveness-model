# iam-control-effectiveness-model

> **Modelo de mensuração de efetividade de controles IAM — da evidência técnica à decisão auditável.**

Este repositório não é uma ferramenta de IAM e não depende de nenhuma plataforma específica.

É a camada de saída de um programa de governança de identidades: transforma dados brutos de acesso em scores de controle ISO, indicadores executivos (KPI/KRI) e estimativa de exposição financeira — com rastreabilidade completa de cada decisão tomada pelo analista.

---

## O que este modelo entrega

| Saída | Descrição | Destinatário |
|---|---|---|
| Score de efetividade por controle ISO | Nota 0–10 por dimensão: RBAC, PAM, SoD, Review, Evidence | Analista / GRC |
| Avaliação de risco ISO 27001 + LGPD | Achados com artigo LGPD, prioridade e decisão sugerida | Analista / Jurídico |
| KPI operacionais | Eficiência do processo de governança por ciclo | Gestor / CISO |
| KRI de exposição | Indicadores de deterioração e concentração de risco | CISO / Board |
| Estimativa de exposição financeira | Custo anual estimado do risco não tratado (FAIR-inspired) | CFO / Board |
| Relatório auditável | Documento autossuficiente com cadeia de evidência SHA-1 | Auditoria / Compliance |

---

## Premissa de design

Qualquer organização pode aplicar este modelo se conseguir expressar seus dados de acesso no formato:

```
control, metric, value, unit, cycle_id, cycle_date, source
```

A plataforma de origem é irrelevante. O modelo já foi validado com evidências de SAP GRC, Salesforce, TOTVS Protheus e Entra ID. O fluxo é sempre o mesmo:

```
Extração → Evidência (SHA-1) → Métrica → Score → KPI/KRI → Decisão → Relatório
```

---

## Dimensões mensuradas

| Dimensão | Código | O que é avaliado | Controles ISO 27001:2022 |
|---|---|---|---|
| Estrutura de acesso | RBAC | Organização de acessos por grupo e role — acúmulo vs. governança | 5.15 · 8.3 |
| Contas privilegiadas | PAM | Exposição por contas sem MFA, sem revisão ou inativas | 8.2 |
| Segregação de funções | SoD | Conflitos ativos e percentual sem tratamento | 5.3 |
| Ciclo de revisão | Review | Completude e prazo das revisões de acesso | 5.18 |
| Rastreabilidade | Evidence | Capacidade de demonstrar conformidade com evidência ligada à decisão | 5.33 |

---

## Camada KPI / KRI

Os KPIs e KRIs não são métricas novas. São os mesmos dados já ingeridos pelo modelo, reorganizados em duas leituras distintas para audiências diferentes.

### KPI — eficiência operacional

Respondem: **o controle está sendo executado conforme esperado?**

| Indicador | Origem | Verde | Amarelo | Vermelho |
|---|---|---|---|---|
| `reviews_completed_pct` | Review | ≥ 90% | 75–89% | < 75% |
| `avg_resolution_days` | SoD | ≤ 15 d | 16–30 d | > 30 d |
| `decisions_with_evidence_pct` | Evidence | ≥ 90% | 75–89% | < 75% |
| `exceptions_documented_pct` | Evidence | ≥ 90% | 75–89% | < 75% |

### KRI — exposição a risco

Respondem: **onde o risco está se acumulando e sem resposta?**

| Indicador | Origem | Verde | Amarelo | Vermelho |
|---|---|---|---|---|
| `conflicts_critical` | SoD | 0 | 1–5 | > 5 |
| `untreated_pct` | SoD | ≤ 10% | 11–30% | > 30% |
| `mfa_coverage_pct` | PAM | ≥ 95% | 85–94% | < 85% |
| `inactive_accounts_pct` | PAM | ≤ 5% | 6–10% | > 10% |

**Leitura combinada:** um KPI alto com KRI alto não é sinal de controle — é sinal de processo operando sobre risco acumulado não tratado. O modelo apresenta os dois painéis lado a lado para que essa tensão seja visível.

---

## Camada de exposição financeira (FAIR-inspired)

Esta camada reutiliza os dados de SoD já ingeridos para produzir uma estimativa de exposição financeira anual associada aos conflitos críticos não tratados.

**Ela responde uma pergunta específica:** quanto custa, por ano, manter este conflito ativo sem tratamento?

### Como funciona

```
Exposição anual = conflitos_críticos × untreated_pct × frequência_estimada × magnitude_por_evento
```

A lógica é inspirada no FAIR (Factor Analysis of Information Risk), mas aplicada como aproximação determinística — não probabilística. Isso significa que o resultado é uma **estimativa de ordem de grandeza**, não uma projeção atuarial.

**O parâmetro que mais importa — e que não vem dos dados — é a magnitude de perda por evento.** O default de R$ 80.000 é um valor conservador baseado em perda primária + custo de resposta a incidente. Cada organização deve calibrar esse valor com base em seus próprios dados históricos ou benchmarks setoriais antes de levar o número a uma audiência executiva.

### Premissas padrão

| Parâmetro | Valor padrão | Como calibrar |
|---|---|---|
| Magnitude por evento | R$ 80.000 | Histórico de incidentes ou benchmark setorial |
| Intervalo entre eventos | 24 meses | Frequência observada de uso indevido de acesso |
| Redução com tratamento | 90% | Baseado em controle compensatório implementado |
| Custo de controle | R$ 20.000 | Custo real do projeto de remediação |

### Exemplo de leitura

Ciclo com `conflicts_critical = 12` e `untreated_pct = 30%`:

- Conflitos ativos: 3,6
- Frequência estimada: 1,8 eventos/ano
- **Exposição anual: R$ 144.000**
- Exposição residual após tratamento: R$ 14.400
- **ROI do tratamento: 548%**

Sinal sugerido pelo modelo: **TRATAR COM PRIORIDADE**

> Esta estimativa não substitui uma análise FAIR completa. Ela serve para priorizar conversas com gestores e demonstrar ordem de grandeza de exposição a partir da evidência operacional já disponível.

---

## Camada LGPD

Cada achado de risco é mapeado para o artigo correspondente da Lei 13.709/2018. Falhas em SoD, PAM, ciclo de revisão e rastreabilidade geram achados com tipo de risco regulatório e decisão sugerida.

O analista confirma ou ajusta cada decisão antes do export. Essa confirmação fica registrada no ciclo — garantindo rastreabilidade da decisão humana sobre cada risco identificado.

---

## Cadeia de evidência

```
Extração → Hash SHA-1 → Ingestão → Score → KPI/KRI → Avaliação → Decisão → Persistência → Relatório
```

O relatório exportado pelo dashboard é autossuficiente para fins de auditoria: contém o manifesto de ingestão com hash, os scores por controle, os indicadores KPI/KRI, o resumo financeiro e cada decisão confirmada pelo analista com justificativa e timestamp.

---

## Posicionamento na série

| Repositório | Camada | Responde |
|---|---|---|
| [iso27001-iam-governance](https://github.com/gilbertocrv/iso27001-iam-governance) | Governança | O que deve existir? |
| [iam-risk-engineering-toolkit](https://github.com/gilbertocrv/iam-risk-engineering-toolkit) | Engenharia | Como estruturar e classificar o risco? |
| [iam-operational-cycle-toolkit](https://github.com/gilbertocrv/iam-operational-cycle-toolkit) | Operação | Como executar e evidenciar o ciclo? |
| **iam-control-effectiveness-model** | **Mensuração** | **O controle está funcionando? Qual o custo se não estiver?** |

---

## Estrutura do repositório

```
iam-control-effectiveness-model/
│
├── index.html                        # Visão geral do modelo e navegação da série
├── tools/
│   └── dashboard.html                # Dashboard v3.0 — Score · KPI/KRI · FAIR · Decisão · Export
├── docs/
│   ├── risk-model.md                 # Regras de avaliação ISO 27001 + LGPD e thresholds
│   ├── data-model.md                 # Especificação dos formatos de entrada e saída
│   ├── kpi-kri-layer.md              # Camada KPI/KRI — thresholds, leitura e uso correto
│   ├── fair-financial-impact.md      # Conector FAIR-inspired — lógica, premissas e limites
│   ├── template-sap-grc.md           # Extração e conversão: SAP GRC (ARA · SUIM · EAM)
│   ├── template-salesforce.md        # Extração e conversão: Salesforce
│   └── template-totvs.md             # Extração e conversão: TOTVS Protheus
├── scripts/
│   ├── kpi_kri_mapper.py             # Reorganiza métricas de um ciclo em KPI e KRI
│   ├── fair_impact_connector.py      # Estima exposição financeira a partir de dados SoD
│   ├── sap_to_metrics.py             # Conversão SAP GRC → metrics.csv
│   ├── salesforce_to_metrics.py      # Conversão Salesforce → metrics.csv
│   └── totvs_to_metrics.py           # Conversão TOTVS → metrics.csv
├── samples/                          # Evidências fictícias para exploração do modelo
└── .github/workflows/
    └── convert-metrics.yml           # Conversão automática no push
```

---

## Premissas e limites

- Processamento 100% local — navegador e Python stdlib. Nenhum dado enviado a servidores externos.
- Os thresholds de KPI/KRI e os defaults de exposição financeira são pontos de partida, não valores absolutos. Cada organização deve calibrá-los com base em seus próprios ciclos e histórico.
- O conector FAIR-inspired produz estimativas de ordem de grandeza. Não substitui uma análise FAIR completa para decisões de investimento em segurança.
- Conteúdo educacional baseado em normas públicas. Não substitui consultoria técnica ou jurídica especializada.

---

**Autor:** Gilberto Gonçalves dos Santos Filho — IAM · PAM · GRC

[![LinkedIn](https://img.shields.io/badge/LinkedIn-gilberto--filho-0077b5?style=flat-square&logo=linkedin)](https://linkedin.com/in/gilberto-filho-4430a3184)
[![GitHub](https://img.shields.io/badge/GitHub-gilbertocrv-333?style=flat-square&logo=github)](https://github.com/gilbertocrv)
