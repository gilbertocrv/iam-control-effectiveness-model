> **Este projeto implementa um modelo de mensuração de efetividade de controles IAM baseado em evidência.**

---

# Modelo de dados — IAM Control Effectiveness Model

## Visão geral

O modelo aceita dois formatos de entrada e produz quatro formatos de saída. Todos os arquivos são texto puro (JSON ou CSV), processados localmente no navegador.

---

## Entrada

### cycles.json — formato nativo

Array de objetos, um por ciclo de revisão.

```json
[
  {
    "cycle_id": "2026-Q1",          // identificador único do ciclo (string)
    "cycle_date": "2026-03-01",     // data de referência (YYYY-MM-DD)
    "source_file": "string",        // origem dos dados
    "imported_at": "ISO-8601",      // timestamp de ingestão
    "controls": {
      "rbac": {
        "control_refs": ["5.15","8.3"],
        "access_via_group_pct":    0-100,
        "direct_access_pct":       0-100,
        "groups_without_owner":    integer,
        "users_multiple_roles_pct": 0-100,
        "score":                   0.0-10.0   // opcional — calculado automaticamente se ausente
      },
      "pam": {
        "control_refs": ["8.2"],
        "privileged_accounts":        integer,
        "mfa_coverage_pct":           0-100,
        "inactive_accounts_pct":      0-100,
        "critical_service_principals": integer,
        "score":                      0.0-10.0
      },
      "sod": {
        "control_refs": ["5.3"],
        "conflicts_total":    integer,
        "conflicts_critical": integer,
        "conflicts_medium":   integer,
        "conflicts_low":      integer,
        "untreated_pct":      0-100,
        "avg_resolution_days": number,
        "score":              0.0-10.0
      },
      "review": {
        "control_refs": ["5.18"],
        "reviews_completed_pct": 0-100,
        "reviews_overdue_pct":   0-100,
        "revocation_rate_pct":   0-100,
        "maintenance_rate_pct":  0-100,
        "score":                 0.0-10.0
      },
      "evidence": {
        "control_refs": ["5.33"],
        "decisions_with_evidence_pct": 0-100,
        "exceptions_documented_pct":   0-100,
        "complete_records_pct":        0-100,
        "avg_report_hours":            number,
        "score":                       0.0-10.0
      }
    },
    "summary": {
      "total_accesses":  integer,
      "overall_score":   0.0-10.0,
      "residual_risk":   "CRÍTICO" | "ALTO" | "MÉDIO" | "BAIXO"
    }
  }
]
```

### metrics.csv — formato por controle

Uma linha por métrica. Colunas obrigatórias:

| Coluna | Tipo | Descrição |
|---|---|---|
| `control` | string | Número do controle ISO (ex: `5.15`, `8.2`) |
| `metric` | string | Nome da métrica (ver tabela abaixo) |
| `value` | number | Valor numérico |
| `unit` | string | `percent` · `count` · `days` · `hours` |
| `cycle_id` | string | Identificador do ciclo |
| `cycle_date` | string | Data de referência (YYYY-MM-DD) |
| `source` | string | Ferramenta de origem |

#### Métricas aceitas no CSV

| metric | Controle | Unidade |
|---|---|---|
| `access_via_group_pct` | 5.15 | percent |
| `direct_access_pct` | 5.15 | percent |
| `groups_without_owner` | 8.3 | count |
| `users_multiple_roles_pct` | 8.3 | percent |
| `privileged_accounts` | 8.2 | count |
| `mfa_coverage_pct` | 8.2 | percent |
| `inactive_accounts_pct` | 8.2 | percent |
| `critical_service_principals` | 8.2 | count |
| `conflicts_total` | 5.3 | count |
| `conflicts_critical` | 5.3 | count |
| `conflicts_medium` | 5.3 | count |
| `conflicts_low` | 5.3 | count |
| `untreated_pct` | 5.3 | percent |
| `avg_resolution_days` | 5.3 | days |
| `reviews_completed_pct` | 5.18 | percent |
| `reviews_overdue_pct` | 5.18 | percent |
| `revocation_rate_pct` | 5.18 | percent |
| `maintenance_rate_pct` | 5.18 | percent |
| `decisions_with_evidence_pct` | 5.33 | percent |
| `exceptions_documented_pct` | 5.33 | percent |
| `complete_records_pct` | 5.33 | percent |
| `avg_report_hours` | 5.33 | hours |

---

## Cálculo automático de scores

Se o campo `score` estiver ausente, o modelo calcula automaticamente:

| Dimensão | Fórmula |
|---|---|
| RBAC | `(access_via_group_pct/10 + max(0, 10 - groups_without_owner×0.3)) / 2` |
| PAM | `(mfa_coverage_pct/10 + max(0, 10 - inactive_accounts_pct×0.4)) / 2` |
| SoD | `(max(0,10 - untreated_pct×0.15) + max(0,10 - avg_resolution_days×0.2)) / 2` |
| Review | `reviews_completed_pct / 10` |
| Evidence | `(decisions_with_evidence_pct + complete_records_pct) / 2 / 10` |
| **Overall** | Média simples das 5 dimensões |

---

## Saída

| Arquivo | Formato | Conteúdo |
|---|---|---|
| `iam-snapshot-{ciclo}.json` | JSON | Ciclo atual + metadados de export |
| `iam-metrics-{ciclo}.csv` | CSV | Métricas do ciclo atual |
| `iam-history.json` | JSON | Todos os ciclos + manifesto |
| `iam-audit-report-{ciclo}.html` | HTML | Relatório autossuficiente para auditor |
| `iam-manifest.csv` | CSV | Registro de importações da sessão |

---

## Manifesto de auditoria

Cada ingestão registra:

| Campo | Descrição |
|---|---|
| `timestamp` | Data e hora UTC da ingestão |
| `filename` | Nome do arquivo importado |
| `type` | `json` ou `csv` |
| `cycles_imported` | Total de ciclos no arquivo |
| `added` | Ciclos novos adicionados |
| `skipped` | Ciclos ignorados (já existentes ou inválidos) |
| `hash` | SHA-1 (12 chars) do conteúdo do arquivo |
| `source` | Origem inferida |

O hash SHA-1 permite verificar que o arquivo importado não foi alterado entre a coleta e a análise — requisito em ambientes regulados.
