> **Este projeto implementa um modelo de mensuração de efetividade de controles IAM baseado em evidência.**
> Este documento descreve um exemplo de conversão para a plataforma TOTVS. O modelo é agnóstico — qualquer plataforma que gere o formato `control, metric, value, unit, cycle_id, cycle_date, source` é compatível.

---

# Template de Extração — TOTVS Protheus

**Plataforma:** TOTVS Protheus 12.x (SigaCFG + módulos integrados)  
**Fontes:** Configurador (SIGACFG) · Tabelas SYS_USR / SIGAPBF / ADS · Logs USR_LSTLOG  
**Controles ISO:** 5.3 · 5.15 · 8.2 · 8.3  
**Exemplo de conversão:** `scripts/totvs_to_metrics.py`  
**Foco regulatório:** LGPD · Resolução BACEN · TCU (ambientes de auditoria pública)

---

## Pré-requisitos

- Acesso ao módulo Configurador (00 – SIGACFG) com perfil de segurança
- Acesso de leitura ao banco de dados para execução de queries SQL
- SGBD: SQL Server, Oracle ou Informix (ajuste a sintaxe conforme o ambiente)

---

## 1. SYS_USR — Cadastro de Usuários

**Módulo:** Configurador (SIGACFG) → Segurança → Usuários  
**Alternativa:** Query direta nas tabelas `SYS_USR` e `SIGAPBF`  
**Alimenta:** `totvs_sys_usr.csv`  
**Métricas geradas:** `access_via_group_pct` · `direct_access_pct` · `privileged_accounts` · `inactive_accounts_pct` · `groups_without_owner`

### Query SQL sugerida (SQL Server)

```sql
SELECT
    u.USR_CODE,
    u.USR_NAME,
    u.USR_GROUP,
    g.GRP_DESC   AS USR_GROUPNAME,
    u.USR_STATUS,               -- 1 = ativo, 0 = inativo
    u.USR_DTLAST,               -- formato YYYYMMDD — último login
    u.USR_TYPE,                 -- 'S' = supervisor/admin, 'N' = normal
    u.USR_OWNER,                -- responsável/gestor do usuário
    u.USR_EMAIL,
    u.USR_DEPT
FROM
    SYS_USR u
LEFT JOIN
    SYS_GRP g ON g.GRP_CODE = u.USR_GROUP
WHERE
    u.USR_STATUS = '1'          -- somente usuários ativos
    AND u.D_E_L_E_T_ = ' '     -- excluir registros marcados para deleção (padrão Protheus)
ORDER BY
    u.USR_GROUP, u.USR_CODE
```

### Colunas esperadas

| Coluna TOTVS | Coluna do template | Tipo | Descrição |
|---|---|---|---|
| USR_CODE | USR_CODE | String | Código do usuário |
| USR_NAME | USR_NAME | String | Nome completo |
| USR_GROUP | USR_GROUP | String | Código do grupo de acesso |
| GRP_DESC | USR_GROUPNAME | String | Descrição do grupo |
| USR_STATUS | USR_STATUS | Char | 1 = ativo |
| USR_DTLAST | USR_DTLAST | YYYYMMDD | Data do último acesso |
| USR_TYPE | USR_TYPE | Char | S = admin / N = normal |
| USR_OWNER | USR_OWNER | String | Gestor responsável (Owner) |

> **Campo USR_OWNER:** O TOTVS não possui um campo nativo de "owner de grupo" — a convenção recomendada é utilizar o campo de observação (`USR_OBS`) ou um campo customizado (UF_) para registrar o gestor responsável. Adapte a query se sua implementação usar outra convenção.

---

## 2. ADS — Dicionário de Acessos (SoD)

**Tabela:** `SIGAPBF` (privilégios por usuário) cruzada com matriz de conflitos  
**Alimenta:** `totvs_sod_conflicts.csv`  
**Métricas geradas:** `conflicts_total` · `conflicts_critical` · `conflicts_medium` · `conflicts_low` · `untreated_pct`

> **Atenção:** O TOTVS Protheus não possui um motor nativo de análise de SoD como o SAP GRC ARA. A identificação de conflitos é feita por query SQL que cruza permissões de rotinas conflitantes com base em uma **matriz de risco definida manualmente**.

### Passo 1 — Definir a matriz de conflitos

Crie um arquivo ou tabela com os pares de rotinas conflitantes:

| ROTINA_A | ROTINA_B | CONFLICT_TYPE | SEVERITY |
|---|---|---|---|
| FINA010 | FINA030 | AP_PAYMENT | Critical |
| COMP010 | COMP030 | PO_GR | High |
| RH010 | RH030 | HR_PAYROLL | Critical |
| ESTO010 | ESTO030 | STOCK_ADJ | High |
| COMP010 | COMP020 | PO_APPROVAL | Medium |

Adapte a lista conforme o mapeamento de processos do cliente.

### Passo 2 — Query SQL de cruzamento (SQL Server)

```sql
-- Identifica usuários com acesso a pares de rotinas conflitantes
SELECT
    a.USR_CODE,
    a.USR_NAME,
    p1.PBF_ROTINA  AS ROTINA_A,
    r1.ADS_DESC    AS DESC_ROTINA_A,
    p2.PBF_ROTINA  AS ROTINA_B,
    r2.ADS_DESC    AS DESC_ROTINA_B,
    'SOD_CONFLICT' AS CONFLICT_TYPE,
    CASE
        WHEN p1.PBF_ROTINA IN ('FINA010','RH010') THEN 'Critical'
        WHEN p1.PBF_ROTINA IN ('COMP010','ESTO010') THEN 'High'
        ELSE 'Medium'
    END AS SEVERITY
FROM
    SYS_USR a
    -- Acesso à rotina A
    JOIN SIGAPBF p1 ON p1.PBF_USER = a.USR_CODE
                    AND p1.D_E_L_E_T_ = ' '
                    AND p1.PBF_ROTINA IN ('FINA010','COMP010','RH010','ESTO010')
    -- Acesso à rotina B conflitante
    JOIN SIGAPBF p2 ON p2.PBF_USER = a.USR_CODE
                    AND p2.D_E_L_E_T_ = ' '
                    AND p2.PBF_ROTINA IN ('FINA030','COMP030','RH030','ESTO030','COMP020')
    -- Garante que é um par conflitante (evita falso positivo)
    JOIN (VALUES
        ('FINA010','FINA030'),
        ('COMP010','COMP030'),
        ('RH010','RH030'),
        ('ESTO010','ESTO030'),
        ('COMP010','COMP020')
    ) AS conflitos(rot_a, rot_b) ON p1.PBF_ROTINA = conflitos.rot_a
                                 AND p2.PBF_ROTINA = conflitos.rot_b
    -- Descrições (opcional — da tabela ADS do dicionário)
    LEFT JOIN ADS r1 ON r1.ADS_ROTINA = p1.PBF_ROTINA AND r1.D_E_L_E_T_ = ' '
    LEFT JOIN ADS r2 ON r2.ADS_ROTINA = p2.PBF_ROTINA AND r2.D_E_L_E_T_ = ' '
WHERE
    a.USR_STATUS = '1'
    AND a.D_E_L_E_T_ = ' '
ORDER BY
    SEVERITY, a.USR_CODE
```

### Colunas esperadas

| Coluna | Tipo | Descrição |
|---|---|---|
| USR_CODE | String | Código do usuário |
| USR_NAME | String | Nome do usuário |
| ROTINA_A | String | Código da rotina conflitante A |
| DESC_ROTINA_A | String | Descrição da rotina A |
| ROTINA_B | String | Código da rotina conflitante B |
| DESC_ROTINA_B | String | Descrição da rotina B |
| CONFLICT_TYPE | String | Tipo de conflito (identificador) |
| SEVERITY | String | Critical / High / Medium / Low |

---

## 3. USR_LSTLOG — Log de Acessos (complementar)

**Tabela:** `USR_LSTLOG` ou relatório do Configurador → Segurança → Log de Acesso  
**Uso:** Complementar — validação de `inactive_accounts_pct` e auditabilidade  
**Métricas complementares:** `avg_report_hours` · evidência de `reviews_completed_pct`

```sql
-- Último acesso por usuário (alternativa ao USR_DTLAST)
SELECT
    l.LOG_USER,
    u.USR_NAME,
    MAX(l.LOG_DATE) AS LAST_ACCESS_DATE,
    DATEDIFF(DAY, MAX(l.LOG_DATE), GETDATE()) AS DAYS_INACTIVE
FROM
    USR_LSTLOG l
    JOIN SYS_USR u ON u.USR_CODE = l.LOG_USER
WHERE
    u.USR_STATUS = '1'
    AND l.D_E_L_E_T_ = ' '
GROUP BY
    l.LOG_USER, u.USR_NAME
HAVING
    DATEDIFF(DAY, MAX(l.LOG_DATE), GETDATE()) > 90
ORDER BY
    DAYS_INACTIVE DESC
```

---

## Execução do exemplo de conversão

```bash
# Converter usuários + conflitos TOTVS
python scripts/totvs_to_metrics.py \
  --users     samples/totvs/totvs_sys_usr.csv \
  --conflicts samples/totvs/totvs_sod_conflicts.csv \
  --cycle     2026-Q1 \
  --date      2026-03-31 \
  --out       samples/totvs/metrics_totvs.csv

# Ajustar threshold de inatividade para 60 dias
python scripts/totvs_to_metrics.py \
  --users     samples/totvs/totvs_sys_usr.csv \
  --cycle     2026-Q1 \
  --date      2026-03-31 \
  --inactive-days 60 \
  --out       samples/metrics.csv \
  --append
```

---

## Mapeamento de métricas

| Métrica do modelo | Fonte TOTVS | Cálculo |
|---|---|---|
| `access_via_group_pct` | SYS_USR | `Usuários com USR_GROUP / Total × 100` |
| `direct_access_pct` | SYS_USR | `Usuários sem grupo / Total × 100` |
| `privileged_accounts` | SYS_USR | Usuários com `USR_TYPE = 'S'` |
| `inactive_accounts_pct` | SYS_USR | `USR_DTLAST > 90d / Total × 100` |
| `groups_without_owner` | SYS_USR | Grupos sem `USR_OWNER` definido |
| `conflicts_total` | SIGAPBF/ADS | Total de linhas no resultado da query |
| `conflicts_critical` | SIGAPBF/ADS | Linhas com `SEVERITY` = Critical ou High |
| `conflicts_medium` | SIGAPBF/ADS | Linhas com `SEVERITY` = Medium |
| `untreated_pct` | SIGAPBF/ADS | 100% (sem motor de SoD nativo) |

---

## Considerações sobre conformidade LGPD

Em ambientes sujeitos à LGPD, o TOTVS Protheus frequentemente contém dados pessoais nos módulos de RH e Financeiro. Ao executar extrações para fins de auditoria IAM:

- Utilize apenas os campos mínimos necessários (minimização de dados — LGPD Art. 6º, IV)
- Não exporte campos como CPF, endereço ou dados de saúde nas extrações de auditoria IAM
- Registre a finalidade da extração no manifesto de auditoria do modelo
- Assegure que os arquivos CSV gerados sejam armazenados em local com controle de acesso adequado

*Baseado em documentação pública TOTVS. Não inclui configurações ou dados de sistemas reais.*
