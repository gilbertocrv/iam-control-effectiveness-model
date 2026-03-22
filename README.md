# iam-governance-dashboard

> **Este projeto implementa um modelo de mensuração de controles de IAM baseado na ISO/IEC 27001:2022.**
>
> Não é uma ferramenta de IAM.
>
> É uma camada de abstração que transforma dados técnicos em indicadores de governança auditável, independente da tecnologia utilizada.

---

## Diferencial do modelo

O dashboard não mede sistemas.

Ele mede:

- **qualidade da estrutura de acesso** — o acesso está organizado ou é um acúmulo sem governança?
- **exposição ao risco** — onde estão as credenciais sem controle, os conflitos de função, os acessos não revisados?
- **efetividade da governança** — as revisões acontecem? As decisões são registradas?
- **capacidade de auditoria** — existe evidência rastreável do dado bruto à decisão humana?

A fonte dos dados — Entra ID, SAP, Salesforce, TOTVS — é irrelevante.

**O que importa é a evidência.**

---

## Posicionamento

Este projeto demonstra que governança de identidades não depende da ferramenta utilizada.

Depende da capacidade de:

- estruturar acesso
- identificar risco
- gerar evidência
- mensurar controle

Qualquer organização, com qualquer stack tecnológico, pode aplicar este modelo se conseguir extrair dados de acesso em formato estruturado.

---

## Camadas do projeto

```
Camada 1 — Governança (ISO 27001)
→ define o que deve ser controlado
→ repositório: iso27001-iam-governance

Camada 2 — Engenharia (RBAC · PAM · SoD)
→ estrutura, criticidade e risco
→ repositório: iam-risk-engineering-toolkit

Camada 3 — Operação (ciclo de revisão)
→ evidência e decisão
→ repositório: iam-operational-cycle-toolkit

Camada 4 — Métricas (este repositório)
→ mensuração da efetividade dos controles
→ repositório: iam-governance-dashboard
```

Cada camada produz artefatos que alimentam a próxima. O dashboard é a camada de saída — onde os dados se tornam indicadores e os indicadores se tornam decisão auditável.

---

## O que este projeto entrega

| Dimensão | O que é medido | Controles ISO |
|---|---|---|
| Estrutura RBAC | Qualidade da organização de acessos por grupo e role | 5.15 · 8.3 |
| Criticidade PAM | Exposição por contas privilegiadas sem MFA ou sem revisão | 8.2 |
| Risco SoD | Conflitos de segregação de funções ativos e sem tratamento | 5.3 |
| Governança Review | Efetividade do ciclo de revisão de acessos | 5.18 |
| Auditabilidade | Capacidade de demonstrar conformidade com evidência rastreável | 5.33 |

---

## Camada LGPD

Além da mensuração ISO, o modelo mapeia o impacto regulatório de cada falha de controle com base na Lei 13.709/2018.

Falhas em SoD, PAM, revisão e evidência geram achados com artigo LGPD correspondente, tipo de risco regulatório e decisão sugerida. O analista confirma ou ajusta cada decisão antes do export — garantindo rastreabilidade da decisão humana sobre o risco identificado.

---

## Conectores — nota conceitual importante

Os conectores (SAP GRC, Salesforce, TOTVS, Entra ID) **não fazem parte do core do projeto**.

Eles existem apenas como exemplos de como extrair evidência técnica de plataformas comuns e traduzi-la para o formato de métricas que o modelo entende.

O modelo é agnóstico. Funciona com qualquer fonte de dados que possa ser expressa como:

```
control, metric, value, unit, cycle_id, cycle_date, source
```

Se você consegue gerar esse CSV — de qualquer sistema — o dashboard processa, avalia e exporta evidência auditável.

---

## Estrutura do repositório

```
iam-governance-dashboard/
│
├── index.html                          # Página principal — visão geral e índice
│
├── tools/
│   └── dashboard.html                  # Dashboard interativo — importação, análise e export
│
├── scripts/                            # Exemplos de conversão por plataforma
│   ├── sap_to_metrics.py              # SAP GRC (ARA + SUIM + EAM) → metrics.csv
│   ├── salesforce_to_metrics.py       # Salesforce (Users + Audit Trail) → metrics.csv
│   └── totvs_to_metrics.py            # TOTVS Protheus (SYS_USR + ADS) → metrics.csv
│
├── samples/                            # Dados fictícios para explorar o modelo
│   ├── cycles.json                    # 3 ciclos históricos de exemplo
│   ├── metrics.csv                    # Métricas unificadas
│   ├── sap/                           # Extracts SAP fictícios
│   ├── salesforce/                    # Extracts Salesforce fictícios
│   └── totvs/                         # Extracts TOTVS fictícios
│
├── docs/
│   ├── risk-model.md                  # Modelo de risco — regras ISO + LGPD e thresholds
│   ├── data-model.md                  # Especificação do formato JSON e CSV
│   ├── template-sap-grc.md            # Exemplo de extração: SAP GRC
│   ├── template-salesforce.md         # Exemplo de extração: Salesforce
│   └── template-totvs.md             # Exemplo de extração: TOTVS Protheus
│
├── .github/
│   └── workflows/
│       └── convert-metrics.yml        # GitHub Actions — conversão automática no push
│
└── README.md
```

---

## Como usar

### Explorar o modelo
Abra `index.html` no navegador e clique em **Abrir dashboard →**. Use "Carregar dados de exemplo" para explorar o fluxo completo com dados fictícios.

### Alimentar com dados reais
Qualquer sistema que exponha dados de acesso pode ser conectado. O caminho mais direto:

1. Exporte os dados de acesso do seu sistema (CSV, planilha, query SQL)
2. Mapeie as colunas para o formato `control, metric, value, unit, cycle_id, cycle_date, source`
3. Importe no dashboard — o motor de risco avalia automaticamente

### Usar os scripts de exemplo
```bash
# SAP GRC
python scripts/sap_to_metrics.py \
  --ara   samples/sap/sap_ara_violations.csv \
  --suim  samples/sap/sap_suim_users.csv \
  --eam   samples/sap/sap_eam_firefighter.csv \
  --cycle 2026-Q1 --date 2026-03-31 --out metrics.csv

# Salesforce
python scripts/salesforce_to_metrics.py \
  --users  samples/salesforce/sf_users_profiles.csv \
  --audit  samples/salesforce/sf_audit_trail.csv \
  --cycle  2026-Q1 --date 2026-03-31 --out metrics.csv

# TOTVS Protheus
python scripts/totvs_to_metrics.py \
  --users     samples/totvs/totvs_sys_usr.csv \
  --conflicts samples/totvs/totvs_sod_conflicts.csv \
  --cycle     2026-Q1 --date 2026-03-31 --out metrics.csv
```

---

## Cadeia de evidência

O modelo fecha a cadeia de evidência de ponta a ponta:

```
Extração (qualquer sistema)
        ↓ hash SHA-1 registrado no manifesto
Importação no dashboard
        ↓ motor de risco avalia por controle ISO
Decisão sugerida (REMEDIATE · ESCALATE · MITIGATE · ACCEPT)
        ↓ analista confirma com justificativa
Persistência em cycle.risk_decisions
        ↓ incluída em qualquer export subsequente
JSON snapshot · CSV métricas · JSON decisões · HTML relatório auditor
```

Cada export carrega o manifesto de importação (com hash), os scores por controle e as decisões confirmadas. O documento resultante é autossuficiente para fins de auditoria.

---

## Posicionamento na série

| Repositório | Camada | Foco |
|---|---|---|
| [iso27001-iam-governance](https://github.com/gilbertocrv/iso27001-iam-governance) | Governança | Políticas, padrões e controles ISO — *o que deve existir* |
| [iam-risk-engineering-toolkit](https://github.com/gilbertocrv/iam-risk-engineering-toolkit) | Engenharia | RBAC · PAM · SoD — *como estruturar* |
| [iam-operational-cycle-toolkit](https://github.com/gilbertocrv/iam-operational-cycle-toolkit) | Operação | Ciclo de revisão — *como evidenciar* |
| **iam-governance-dashboard** | **Métricas** | **Scores e decisão — *como mensurar*** |

---

## Premissas

- Processamento 100% local — browser (dashboard) e Python stdlib (scripts, sem dependências externas)
- Nenhum dado enviado a servidores externos além do repositório GitHub
- Todo o conteúdo é educacional, baseado em normas públicas

---

*Não substitui consultoria técnica ou jurídica especializada.*

**Autor:** Gilberto Gonçalves dos Santos Filho — IAM · PAM · GRC

[![LinkedIn](https://img.shields.io/badge/LinkedIn-gilberto--filho-0077b5?style=flat-square&logo=linkedin)](https://linkedin.com/in/gilberto-filho-4430a3184)
[![GitHub](https://img.shields.io/badge/GitHub-gilbertocrv-333?style=flat-square&logo=github)](https://github.com/gilbertocrv)
