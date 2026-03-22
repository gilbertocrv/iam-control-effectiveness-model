# iam-governance-dashboard

Dashboard operacional de métricas IAM — scores de efetividade por controle ISO, avaliação de risco com camada LGPD e decisão semi-automática confirmada pelo analista.

**GitHub Pages:** `https://gilbertocrv.github.io/iam-governance-dashboard`

---

## Posicionamento na série

| Série | Foco | Repositório |
|---|---|---|
| Série 2 | Governança — políticas, padrões e controles ISO | [iso27001-iam-governance](https://github.com/gilbertocrv/iso27001-iam-governance) |
| Série 3 — Ciclo | Operação — análise, decisão, registro e evidência | [iam-operational-cycle-toolkit](https://github.com/gilbertocrv/iam-operational-cycle-toolkit) |
| Série 3 — Risco | Estrutura RBAC · PAM · SoD — execução operacional | [iam-risk-engineering-toolkit](https://github.com/gilbertocrv/iam-risk-engineering-toolkit) |
| **Série 3 — Métricas** | **Resultados — scores, histórico e relatório de auditoria** | **iam-governance-dashboard** |

---

## Estrutura do repositório

```
iam-governance-dashboard/
│
├── index.html                          # Página principal — índice e documentação
│
├── tools/
│   └── dashboard.html                  # Dashboard interativo completo
│
├── scripts/
│   ├── sap_to_metrics.py              # SAP GRC (ARA + SUIM + EAM) → metrics.csv
│   ├── salesforce_to_metrics.py       # Salesforce (Users + Audit Trail) → metrics.csv
│   └── totvs_to_metrics.py            # TOTVS Protheus (SYS_USR + ADS) → metrics.csv
│
├── samples/
│   ├── cycles.json                    # 3 ciclos históricos de exemplo
│   ├── metrics.csv                    # Métricas unificadas (gerado pelo workflow)
│   ├── sap/
│   │   ├── sap_ara_violations.csv     # Export ARA — violações SoD
│   │   ├── sap_suim_users.csv         # Export SUIM — usuários e perfis
│   │   └── sap_eam_firefighter.csv    # Export EAM — log Firefighter
│   ├── salesforce/
│   │   ├── sf_users_profiles.csv      # Export Users + Permission Sets
│   │   └── sf_audit_trail.csv         # Export Setup Audit Trail
│   └── totvs/
│       ├── totvs_sys_usr.csv          # Export SYS_USR (query SQL)
│       └── totvs_sod_conflicts.csv    # Export ADS SoD (query SQL)
│
├── docs/
│   ├── risk-model.md                  # Modelo de risco ISO + LGPD — regras e thresholds
│   ├── data-model.md                  # Formato JSON e CSV — campos e cálculos
│   ├── template-sap-grc.md            # Guia de extração SAP GRC
│   ├── template-salesforce.md         # Guia de extração Salesforce
│   └── template-totvs.md             # Guia de extração TOTVS Protheus
│
├── .github/
│   └── workflows/
│       └── convert-metrics.yml        # GitHub Actions — conversão automática no push
│
└── README.md
```

---

## Conectores suportados

| Plataforma | Módulos | Script | Doc |
|---|---|---|---|
| **Microsoft Entra ID** | Access Audit · Recertification · Evidence Register | — (CSV nativo) | — |
| **SAP GRC** | ARA (SoD) · SUIM (RBAC) · EAM (Firefighter) | `scripts/sap_to_metrics.py` | `docs/template-sap-grc.md` |
| **Salesforce** | Users + Profiles · Setup Audit Trail | `scripts/salesforce_to_metrics.py` | `docs/template-salesforce.md` |
| **TOTVS Protheus** | SYS_USR · SIGAPBF · ADS (SoD via SQL) | `scripts/totvs_to_metrics.py` | `docs/template-totvs.md` |

---

## Como usar

### GitHub Pages
1. Fork ou clone o repositório
2. Acesse `Settings → Pages → Branch: main → /(root)`
3. Acesse `https://{seu-usuario}.github.io/iam-governance-dashboard`

### Localmente
Abra `index.html` no navegador. Clique em **Abrir dashboard →** para acessar a ferramenta.

### Importar dados reais
```bash
# SAP GRC
python scripts/sap_to_metrics.py \
  --ara   samples/sap/sap_ara_violations.csv \
  --suim  samples/sap/sap_suim_users.csv \
  --eam   samples/sap/sap_eam_firefighter.csv \
  --cycle 2026-Q1 --date 2026-03-31 --out samples/sap/metrics_sap.csv

# Salesforce
python scripts/salesforce_to_metrics.py \
  --users  samples/salesforce/sf_users_profiles.csv \
  --audit  samples/salesforce/sf_audit_trail.csv \
  --cycle  2026-Q1 --date 2026-03-31 --out samples/salesforce/metrics_salesforce.csv

# TOTVS Protheus
python scripts/totvs_to_metrics.py \
  --users     samples/totvs/totvs_sys_usr.csv \
  --conflicts samples/totvs/totvs_sod_conflicts.csv \
  --cycle     2026-Q1 --date 2026-03-31 --out samples/totvs/metrics_totvs.csv
```

---

## GitHub Actions — conversão automática

O workflow `convert-metrics.yml` executa ao fazer push em `samples/` ou `scripts/`.
Também disponível via **workflow_dispatch** para execução manual com seleção de ciclo e plataforma.

---

## Controles ISO/IEC 27001:2022 cobertos

| Controle | Dimensão | Plataformas |
|---|---|---|
| 5.3 | Segregação de Funções (SoD) | SAP ARA · TOTVS ADS |
| 5.15 · 8.3 | Estrutura RBAC | SAP SUIM · Salesforce · TOTVS · Entra ID |
| 5.18 | Revisão de Acessos | Entra ID · Recertification |
| 5.33 | Auditabilidade e Evidência | SAP EAM · Salesforce Audit Trail · Evidence Register |
| 8.2 | Acesso Privilegiado (PAM) | SAP EAM/SUIM · Salesforce · TOTVS · Entra ID |

---

## Premissas

- Processamento 100% local — browser (dashboard) e Python stdlib (scripts)
- Nenhum dado enviado a servidores externos além do repositório GitHub
- Scripts sem dependências externas (somente biblioteca padrão Python)

---

*Conteúdo educacional independente baseado em normas públicas. Não substitui consultoria técnica ou jurídica especializada.*

**Autor:** Gilberto Gonçalves dos Santos Filho — IAM · PAM · GRC

[![LinkedIn](https://img.shields.io/badge/LinkedIn-gilberto--filho-0077b5?style=flat-square&logo=linkedin)](https://linkedin.com/in/gilberto-filho-4430a3184)
[![GitHub](https://img.shields.io/badge/GitHub-gilbertocrv-333?style=flat-square&logo=github)](https://github.com/gilbertocrv)
