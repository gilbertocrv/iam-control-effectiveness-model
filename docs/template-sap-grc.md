# Template de Extração — SAP GRC (Access Control)

**Plataforma:** SAP GRC 10.x / 12.x  
**Módulos:** ARA (Access Risk Analysis) · EAM (Emergency Access Management) · SUIM  
**Controles ISO:** 5.3 · 5.15 · 5.18 · 5.33 · 8.2 · 8.3  
**Script de conversão:** `scripts/sap_to_metrics.py`

---

## Pré-requisitos

- Acesso de leitura ao sistema SAP GRC
- Autorização nos objetos: `S_TABU_DIS` (grupos de tabelas GRC*) e `S_TCODE` para as transações abaixo
- Acesso ao módulo ARA com permissão de execução de relatórios

---

## 1. ARA — Violações de Segregação de Funções

**Transação:** `/GRCPI/GRIA_SOD_REPT` ou `GRAC_REPORTING`  
**Alimenta:** `sap_ara_violations.csv`  
**Métricas geradas:** `conflicts_total` · `conflicts_critical` · `conflicts_medium` · `conflicts_low` · `untreated_pct`

### Procedimento

1. Acesse a transação `/GRCPI/GRIA_SOD_REPT`
2. Selecione o tipo de relatório: **Access Risk Violation Report**
3. Configure os parâmetros:
   - **Analysis Type:** User Level
   - **Risk Level:** All (Critical, High, Medium, Low)
   - **Status:** All
   - **Date Range:** período do ciclo de revisão
4. Execute e exporte para **CSV/Spreadsheet**

### Colunas esperadas no export

| Coluna SAP | Coluna do template | Descrição |
|---|---|---|
| User ID | UserID | ID do usuário |
| User Name | UserName | Nome completo |
| Risk ID | RiskID | Código da regra de risco |
| Risk Description | RiskDescription | Descrição da violação |
| Risk Level | RiskLevel | Critical / High / Medium / Low |
| Function 1 | Function1 | Código da função/transação A |
| Function 2 | Function2 | Código da função/transação B |
| Rule Set | RuleSet | Conjunto de regras aplicado |
| Mitigating Control | MitigatingControl | Controle mitigador (se aplicável) |
| Mitigation Owner | MitigationOwner | Responsável pela mitigação |
| Status | Status | Open / Mitigated |

> **Nota:** Adapte os cabeçalhos do export SAP para corresponder à coluna do template antes de executar o script. O script aceita variações menores (case-insensitive para `RiskLevel` e `Status`).

---

## 2. SUIM — Usuários e Atribuições de Perfil

**Transação:** `SUIM` → Usuários → Por Autorização de Objeto  
**Alternativa:** `RSUSR002` (programa) ou SE16N nas tabelas `USR02`, `AGR_USERS`  
**Alimenta:** `sap_suim_users.csv`  
**Métricas geradas:** `access_via_group_pct` · `direct_access_pct` · `privileged_accounts` · `inactive_accounts_pct` · `users_multiple_roles_pct`

### Procedimento

1. Execute `SUIM` → **Users → User by Complex Selection Criteria**
2. Selecione todos os usuários ativos (Type: Dialog, System, Service)
3. Exporte as colunas: User ID, User Name, User Type, Profile/Role, Assignment Type, Last Login
4. Para contas inativas: adicione filtro de `Last Login Date` < data do ciclo - 90 dias

### Colunas esperadas

| Coluna SAP | Coluna do template | Descrição |
|---|---|---|
| User | UserID | ID do usuário |
| User Name | UserName | Nome completo |
| User Type | UserType | Dialog / System / Service |
| Department | Department | Departamento |
| Type (Profile/Role) | ProfileType | Profile ou Role |
| Profile/Role Name | ProfileName | Nome do perfil ou role |
| Direct Assignment | AssignedDirectly | Yes / No |
| Last Logon Date | LastLogin | YYYY-MM-DD |
| Locked | AccountStatus | Active / Locked |

> **Atenção:** Perfis atribuídos diretamente (não via role composta) são o principal indicador de **acesso fora do modelo RBAC**. Perfis `SAP_ALL` e `SAP_NEW` atribuídos diretamente a usuários Dialog são achados de auditoria críticos.

---

## 3. EAM — Log de Acesso Firefighter

**Transação:** `GRAC_SPM` → Log Report  
**Alternativa:** Tabelas `GRAC_SPM_LOG_HDR` + `GRAC_SPM_LOG_DTL` via SE16N  
**Alimenta:** `sap_eam_firefighter.csv`  
**Métricas geradas:** `decisions_with_evidence_pct` · `critical_service_principals`

### Procedimento

1. Acesse `GRAC_SPM` → **Firefighter Log Report**
2. Selecione o período do ciclo de revisão
3. Inclua todos os IDs de Firefighter ativos
4. Exporte o log com as colunas de revisão (Reviewed, ReviewDate, ReviewedBy)

### Colunas esperadas

| Coluna SAP | Coluna do template | Descrição |
|---|---|---|
| Log ID | LogID | Identificador do log |
| Firefighter ID | FirefighterID | ID da conta Firefighter |
| Firefighter Name | FirefighterName | Nome da conta |
| Owner ID | OwnerID | ID do usuário que usou |
| Owner Name | OwnerName | Nome do usuário |
| Reason | Reason | Justificativa de uso |
| Start Time | StartTime | YYYY-MM-DD HH:MM |
| End Time | EndTime | YYYY-MM-DD HH:MM |
| Transactions Used | TransactionsUsed | Lista de transações executadas |
| Reviewed | Reviewed | Yes / No |
| Review Date | ReviewDate | Data da revisão |
| Reviewed By | ReviewedBy | Revisor responsável |

> **Ponto crítico de auditoria:** Sessões Firefighter **sem revisão** (`Reviewed = No`) representam uso de acesso privilegiado sem evidência de controle posterior — achado crítico para ISO 27001 controle 8.2.

---

## Execução do script

```bash
# Converter todos os arquivos SAP de uma vez
python scripts/sap_to_metrics.py \
  --ara   samples/sap/sap_ara_violations.csv \
  --suim  samples/sap/sap_suim_users.csv \
  --eam   samples/sap/sap_eam_firefighter.csv \
  --cycle 2026-Q1 \
  --date  2026-03-31 \
  --out   samples/sap/metrics_sap.csv

# Converter apenas ARA (SoD), anexando a um CSV existente
python scripts/sap_to_metrics.py \
  --ara   samples/sap/sap_ara_violations.csv \
  --cycle 2026-Q1 \
  --date  2026-03-31 \
  --out   samples/metrics.csv \
  --append
```

---

## Mapeamento de métricas

| Métrica do dashboard | Fonte SAP | Cálculo |
|---|---|---|
| `conflicts_total` | ARA | Total de linhas no relatório de violações |
| `conflicts_critical` | ARA | Linhas com `RiskLevel` = Critical ou High |
| `conflicts_medium` | ARA | Linhas com `RiskLevel` = Medium |
| `conflicts_low` | ARA | Linhas com `RiskLevel` = Low |
| `untreated_pct` | ARA | `(Total - Mitigated) / Total × 100` |
| `access_via_group_pct` | SUIM | `Usuários sem perfil direto / Total × 100` |
| `direct_access_pct` | SUIM | `Usuários com perfil direto / Total × 100` |
| `privileged_accounts` | SUIM | Usuários tipo System/Service + perfil direto |
| `inactive_accounts_pct` | SUIM | `Usuários sem login >90d / Total × 100` |
| `users_multiple_roles_pct` | SUIM | `Usuários com >1 role / Total × 100` |
| `decisions_with_evidence_pct` | EAM | `Sessões FF revisadas / Total × 100` |
| `critical_service_principals` | EAM | Sessões FF sem revisão (exposição) |

---

## Evidência de auditoria

Para cada extração, registre no manifesto:
- Data e responsável pela extração
- Transação utilizada e parâmetros aplicados
- Hash SHA-1 do arquivo exportado (gerado automaticamente pelo dashboard)
- Período de referência do relatório

*Baseado em normas públicas. Não inclui configurações ou dados de sistemas reais.*
