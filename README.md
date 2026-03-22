# iam-control-effectiveness-model

> **Este projeto implementa um modelo de mensuração de efetividade de controles IAM baseado em evidência.**

Não é uma ferramenta de IAM.

É uma camada de abstração que transforma dados técnicos em indicadores de governança auditável, independente da tecnologia utilizada.

---

## O modelo não mede sistemas

Ele mede:

- **estrutura** — o acesso está organizado ou é um acúmulo sem governança?
- **criticidade** — onde estão as credenciais sem controle, os privilégios sem revisão?
- **risco** — quais conflitos de função estão ativos e sem tratamento?
- **governança** — as revisões acontecem? As decisões são registradas?
- **auditabilidade** — existe evidência rastreável do dado bruto à decisão humana?

A fonte dos dados é irrelevante. **O que importa é a evidência.**

---

## Posicionamento

Este projeto demonstra que governança de identidades não depende da ferramenta utilizada.

Depende da capacidade de estruturar acesso, identificar risco, gerar evidência e mensurar controle.

Qualquer organização, com qualquer stack tecnológico, pode aplicar este modelo se conseguir expressar dados de acesso no formato:

```
control, metric, value, unit, cycle_id, cycle_date, source
```

---

## Fluxo único do modelo

```
Extração → Evidência → Métrica → Avaliação → Decisão
```

| Etapa | O que acontece |
|---|---|
| **Extração** | Dados de acesso exportados de qualquer sistema |
| **Evidência** | Hash SHA-1 registrado — rastreabilidade garantida |
| **Métrica** | Dados normalizados por controle ISO |
| **Avaliação** | Motor de risco avalia por threshold — ISO 27001 + LGPD |
| **Decisão** | Analista confirma com justificativa — persistida no ciclo |

---

## Dimensões mensuradas

| Dimensão | Terminologia | O que é medido | Controles ISO |
|---|---|---|---|
| Estrutura | RBAC | Qualidade da organização de acessos por grupo e role | 5.15 · 8.3 |
| Criticidade | PAM | Exposição por contas privilegiadas sem MFA ou sem revisão | 8.2 |
| Risco | SoD | Conflitos de segregação de funções ativos e sem tratamento | 5.3 |
| Governança | Review | Efetividade do ciclo de revisão de acessos | 5.18 |
| Auditabilidade | Evidence | Capacidade de demonstrar conformidade com evidência rastreável | 5.33 |

---

## Camadas do projeto

```
Camada 1 — Governança    → define o que deve ser controlado
Camada 2 — Engenharia    → estrutura, criticidade e risco
Camada 3 — Operação      → evidência e decisão
Camada 4 — Métricas      → mensuração da efetividade (este repositório)
```

Cada camada produz artefatos que alimentam a próxima. Este modelo é a camada de saída — onde os dados se tornam indicadores e os indicadores se tornam decisão auditável.

---

## Camada LGPD

Além da mensuração ISO, o modelo mapeia o impacto regulatório de cada falha de controle com base na Lei 13.709/2018.

Falhas em SoD, PAM, revisão e evidência geram achados com artigo LGPD correspondente, tipo de risco regulatório e decisão sugerida. O analista confirma ou ajusta cada decisão antes do export — garantindo rastreabilidade da decisão humana sobre o risco identificado.

---

## Exemplos de conversão — nota conceitual

Os exemplos de conversão (SAP GRC, Salesforce, TOTVS, Entra ID) **não fazem parte do core do modelo**.

Existem apenas para demonstrar como extrair evidência técnica de plataformas comuns e traduzi-la para o formato que o modelo entende.

O modelo é agnóstico. A plataforma de origem não importa.

---

## Cadeia de evidência

```
Extração → Hash SHA-1 → Ingestão → Avaliação → Decisão → Persistência → Relatório
```

Cada export carrega o manifesto de ingestão (com hash), os scores por controle e as decisões confirmadas pelo analista. O documento resultante é autossuficiente para fins de auditoria.

---

## Estrutura do repositório

```
iam-control-effectiveness-model/
│
├── index.html                    # Visão geral do modelo
├── tools/
│   └── dashboard.html            # Camada de visualização — ingestão, avaliação e export
├── docs/
│   ├── risk-model.md             # Modelo de risco — regras ISO + LGPD e thresholds
│   ├── data-model.md             # Especificação do formato de evidência
│   ├── template-sap-grc.md       # Exemplo de conversão: SAP GRC
│   ├── template-salesforce.md    # Exemplo de conversão: Salesforce
│   └── template-totvs.md         # Exemplo de conversão: TOTVS Protheus
├── scripts/                      # Exemplos de conversão por plataforma
├── samples/                      # Evidências fictícias para explorar o modelo
└── .github/workflows/
    └── convert-metrics.yml       # Automação de conversão no push
```

---

## Posicionamento na série

| Repositório | Camada | Foco |
|---|---|---|
| [iso27001-iam-governance](https://github.com/gilbertocrv/iso27001-iam-governance) | Governança | Políticas e controles ISO — *o que deve existir* |
| [iam-risk-engineering-toolkit](https://github.com/gilbertocrv/iam-risk-engineering-toolkit) | Engenharia | Estrutura, criticidade e risco — *como organizar* |
| [iam-operational-cycle-toolkit](https://github.com/gilbertocrv/iam-operational-cycle-toolkit) | Operação | Ciclo de revisão — *como evidenciar* |
| **iam-control-effectiveness-model** | **Métricas** | **Mensuração de efetividade — *como medir*** |

---

## Premissas

- Processamento 100% local — navegador (camada de visualização) e Python stdlib (exemplos de conversão)
- Nenhum dado enviado a servidores externos
- Conteúdo educacional baseado em normas públicas

*Não substitui consultoria técnica ou jurídica especializada.*

**Autor:** Gilberto Gonçalves dos Santos Filho — IAM · PAM · GRC

[![LinkedIn](https://img.shields.io/badge/LinkedIn-gilberto--filho-0077b5?style=flat-square&logo=linkedin)](https://linkedin.com/in/gilberto-filho-4430a3184)
[![GitHub](https://img.shields.io/badge/GitHub-gilbertocrv-333?style=flat-square&logo=github)](https://github.com/gilbertocrv)
