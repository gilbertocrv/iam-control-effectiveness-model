# Template de Extração — Salesforce

**Plataforma:** Salesforce (Sales Cloud · Service Cloud · Platform)  
**Fontes:** Reports Builder · Setup Audit Trail · Security Health Check  
**Controles ISO:** 5.15 · 5.33 · 8.2 · 8.3  
**Script de conversão:** `scripts/salesforce_to_metrics.py`

---

## Pré-requisitos

- Perfil System Administrator ou permissão "View Setup and Configuration"
- Acesso ao Setup Audit Trail (últimos 6 meses disponíveis nativamente)
- Permissão "Manage Users" para exportar relatórios de usuários

---

## 1. Users with Profiles and Permission Sets

**Caminho:** Setup → Users → Users → Export  
**Alternativa:** Relatório customizado no Report Builder  
**Alimenta:** `sf_users_profiles.csv`  
**Métricas geradas:** `access_via_group_pct` · `direct_access_pct` · `privileged_accounts` · `mfa_coverage_pct` · `inactive_accounts_pct` · `users_multiple_roles_pct`

### Procedimento

**Opção A — Export direto:**
1. Setup → Users → Users
2. Clique em **Export** (formato CSV)
3. Selecione os campos: User ID, Username, Is Active, Last Login Date, Profile Name, License Type

**Opção B — Relatório customizado (recomendado):**
1. Acesse **Reports** → New Report → Report Type: Users
2. Adicione colunas: User ID, Username, Active, Last Login, Profile, Permission Set Count, MFA Enabled
3. Sem filtro de data (exibir todos os usuários)
4. Exporte em **CSV**

**Para Permission Sets:**
1. Setup → Permission Sets
2. Para cada Permission Set relevante, acesse "Manage Assignments" e exporte

> **Dica:** Use o **Identity Verification History** em Setup → Security → Identity Verification History para exportar dados de MFA por usuário, incluindo método utilizado (Authenticator, SMS, etc.).

### Colunas esperadas

| Coluna Salesforce | Coluna do template | Descrição |
|---|---|---|
| User ID | UserId | ID interno Salesforce (18 chars) |
| Username | Username | email@dominio.com |
| Active | IsActive | true / false |
| Last Login | LastLoginDate | YYYY-MM-DD |
| Profile Name | ProfileName | Nome do perfil atribuído |
| Permission Set Count | PermissionSetCount | Número de Permission Sets |
| Permission Sets | PermissionSets | Lista separada por ponto-e-vírgula |
| MFA Enabled | MfaEnabled | true / false |
| MFA Method | MfaMethod | Authenticator / SMS / etc. |

---

## 2. Setup Audit Trail

**Caminho:** Setup → Security → View Setup Audit Trail  
**Disponibilidade:** Últimos 180 dias (download disponível para últimos 6 meses)  
**Alimenta:** `sf_audit_trail.csv`  
**Métricas geradas:** `decisions_with_evidence_pct` · `exceptions_documented_pct`

### Procedimento

1. Setup → **Security** → **View Setup Audit Trail**
2. Clique em **Download** para baixar o CSV completo do período
3. Alternativamente, filtre por **Section** para focar em Users, Permission Sets e Security

### Colunas esperadas

| Coluna Salesforce | Coluna do template | Descrição |
|---|---|---|
| Date | Date | YYYY-MM-DD HH:MM |
| Action | Action | Tipo da ação (camelCase) |
| Section | Section | Área do Setup |
| User | CreatedByUsername | Quem executou a ação |
| Source IP Address | SourceIp | IP de origem |
| Display | Display | Descrição da alteração |
| *(campo customizado)* | TicketID | ID do chamado (ITSM) — campo custom ou padrão ITIL |

> **Integração com ITSM:** O campo `TicketID` não existe nativamente no Salesforce Audit Trail. Para ambientes com controle de evidência, recomenda-se padronizar o campo **Display** incluindo o número do chamado no formato `[TKT-XXXX]`, ou integrar o Audit Trail com a ferramenta ITSM via Flow/API. O script identifica tickets pelo padrão `TKT-XXXX` ou campo dedicado.

### Ações classificadas como críticas (impactam `exceptions_documented_pct`)

| Action | Descrição |
|---|---|
| `userModified` | Alteração de usuário |
| `permSetAssigned` | Atribuição de Permission Set |
| `permSetRevoked` | Revogação de Permission Set |
| `profileCreated` | Criação de perfil |
| `mfaPolicyModified` | Alteração de política MFA |
| `sessionSettingsModified` | Alteração de configuração de sessão |
| `passwordPolicyModified` | Alteração de política de senha |

---

## 3. Security Health Check (complementar)

**Caminho:** Setup → Security → Health Check  
**Uso:** Validação complementar — não é input direto do script  
**Referência:** Controles 5.15 · 8.2 · 8.5

O Security Health Check fornece um score consolidado de configuração de segurança. Utilize-o como evidência qualitativa complementar ao dashboard — registre o score geral e os itens em status "Meets Recommended Value" vs "Does Not Meet".

---

## Execução do script

```bash
# Converter usuários + audit trail
python scripts/salesforce_to_metrics.py \
  --users  samples/salesforce/sf_users_profiles.csv \
  --audit  samples/salesforce/sf_audit_trail.csv \
  --cycle  2026-Q1 \
  --date   2026-03-31 \
  --out    samples/salesforce/metrics_salesforce.csv

# Converter apenas usuários (sem audit trail)
python scripts/salesforce_to_metrics.py \
  --users  samples/salesforce/sf_users_profiles.csv \
  --cycle  2026-Q1 \
  --date   2026-03-31 \
  --out    samples/metrics.csv \
  --append
```

---

## Mapeamento de métricas

| Métrica do dashboard | Fonte Salesforce | Cálculo |
|---|---|---|
| `access_via_group_pct` | Users | `Usuários não-admin / Total × 100` |
| `direct_access_pct` | Users | `System Administrators / Total × 100` |
| `privileged_accounts` | Users | Contagem de System Administrators ativos |
| `mfa_coverage_pct` | Users | `MfaEnabled = true / Total ativos × 100` |
| `inactive_accounts_pct` | Users | `Ativos sem login >90d / Total ativos × 100` |
| `users_multiple_roles_pct` | Users | `PermissionSetCount > 1 / Total × 100` |
| `decisions_with_evidence_pct` | Audit Trail | `Entradas com TicketID / Total × 100` |
| `exceptions_documented_pct` | Audit Trail | `Ações críticas com TicketID / Total críticas × 100` |

---

*Baseado em documentação pública Salesforce. Não inclui configurações ou dados de sistemas reais.*
