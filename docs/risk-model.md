# Modelo de Risco — ISO 27001:2022 + LGPD

Este documento define as regras de interpretação de risco aplicadas pelo dashboard.  
A ISO/IEC 27001:2022 não prescreve scores ou thresholds — este modelo traduz a **intenção de cada controle** em critérios operacionais mensuráveis, combinados com o impacto regulatório da LGPD (Lei 13.709/2018).

**Versão:** 1.0 · **Referência normativa:** ISO/IEC 27001:2022 Anexo A · LGPD Art. 6º, 46º, 48º, 52º

---

## 1. Mapeamento ISO → Risco

| Controle | Dimensão | Falha identificada | Risco operacional |
|---|---|---|---|
| **5.3** | Segregação de Funções | Conflitos críticos de SoD ativos | Fraude · Bypass de controle interno · Manipulação de dados |
| **5.15** | Controle de Acesso | Acesso direto (fora de grupo/role) | Acesso não rastreável · Violação de princípio do menor privilégio |
| **5.18** | Revisão de Acessos | Revisões não concluídas ou fora do prazo | Acesso acumulado indevido · Permissões obsoletas ativas |
| **8.2** | Acesso Privilegiado | Sem MFA · Contas inativas · Sem revisão EAM | Comprometimento de credencial · Acesso não autorizado a sistemas críticos |
| **8.3** | Restrição de Acesso | Grupos sem owner definido | Governança de acesso sem responsável formal |
| **5.33** | Auditabilidade | Decisões sem evidência · Registros incompletos | Incapacidade de demonstrar conformidade em auditoria |

---

## 2. Mapeamento LGPD → Impacto Regulatório

| Tipo de falha IAM | Artigo LGPD | Impacto regulatório | Risco de sanção |
|---|---|---|---|
| Acesso indevido a dados pessoais (SoD 5.3) | Art. 46º — medidas de segurança | Violação de dados pessoais por acesso não autorizado | Sanção administrativa · Art. 52º |
| Privilégio excessivo sem MFA (8.2) | Art. 46º · Art. 48º (notificação) | Exposição de dados sensíveis por comprometimento de credencial | Notificação à ANPD · Sanção |
| Acesso não revisado (5.18) | Art. 6º, IV — minimização · Art. 46º | Dado pessoal acessado sem base legal vigente | Sanção administrativa |
| Ausência de evidência (5.33) | Art. 6º, X — responsabilização | Falha de accountability — incapacidade de comprovar conformidade | Sanção + agravante em fiscalização |
| Grupos sem owner (8.3) | Art. 46º — responsabilidade | Ausência de responsável formal por acesso a dados pessoais | Risco em auditoria regulatória |

**Referência de sanções (LGPD Art. 52º):**
- Advertência com prazo para adoção de medidas
- Multa simples de até 2% do faturamento (limite R$ 50 milhões por infração)
- Multa diária
- Publicização da infração
- Suspensão parcial ou total do tratamento de dados

---

## 3. Regras de Decisão

As regras abaixo são aplicadas automaticamente pelo dashboard para gerar uma **decisão sugerida**.  
O analista confirma, ajusta ou rejeita a sugestão antes do export.

### 3.1 Controle 5.3 — SoD

| Condição | Decisão sugerida | Prioridade | LGPD trigger |
|---|---|---|---|
| `conflicts_critical > 10` | REMEDIATE | URGENTE | Sim — Art. 46º |
| `conflicts_critical` entre 5 e 10 | MITIGATE | ALTA | Sim |
| `conflicts_critical` entre 1 e 4 | MITIGATE | MÉDIA | Condicional |
| `conflicts_critical = 0` | ACCEPT | BAIXA | Não |
| `untreated_pct > 30%` | REMEDIATE | ALTA | Sim — Art. 46º |
| `untreated_pct` entre 15% e 30% | MITIGATE | MÉDIA | Condicional |
| `avg_resolution_days > 30` | ESCALATE | ALTA | — |

### 3.2 Controle 8.2 — PAM

| Condição | Decisão sugerida | Prioridade | LGPD trigger |
|---|---|---|---|
| `mfa_coverage_pct < 80%` | REMEDIATE | URGENTE | Sim — Art. 46º + 48º |
| `mfa_coverage_pct` entre 80% e 90% | REMEDIATE | ALTA | Sim |
| `mfa_coverage_pct >= 90%` | ACCEPT | BAIXA | Não |
| `inactive_accounts_pct > 15%` | REMEDIATE | ALTA | Sim — Art. 46º |
| `inactive_accounts_pct` entre 10% e 15% | MITIGATE | MÉDIA | Condicional |
| `critical_service_principals > 5` | ESCALATE | ALTA | Sim |

### 3.3 Controle 5.18 — Access Review

| Condição | Decisão sugerida | Prioridade | LGPD trigger |
|---|---|---|---|
| `reviews_completed_pct < 60%` | REMEDIATE | URGENTE | Sim — Art. 6º IV |
| `reviews_completed_pct` entre 60% e 80% | MITIGATE | ALTA | Sim |
| `reviews_completed_pct >= 80%` | ACCEPT | BAIXA | Não |
| `reviews_overdue_pct > 20%` | ESCALATE | ALTA | Sim |
| `reviews_overdue_pct` entre 10% e 20% | MITIGATE | MÉDIA | Condicional |

### 3.4 Controle 5.33 — Evidence

| Condição | Decisão sugerida | Prioridade | LGPD trigger |
|---|---|---|---|
| `decisions_with_evidence_pct < 70%` | REMEDIATE | URGENTE | Sim — Art. 6º X |
| `decisions_with_evidence_pct` entre 70% e 85% | MITIGATE | ALTA | Sim |
| `decisions_with_evidence_pct >= 85%` | ACCEPT | BAIXA | Não |
| `exceptions_documented_pct < 60%` | REMEDIATE | ALTA | Sim — Art. 6º X |
| `complete_records_pct < 80%` | MITIGATE | MÉDIA | Condicional |

---

## 4. Vocabulário de decisões

| Decisão | Significado operacional |
|---|---|
| **REMEDIATE** | Ação corretiva imediata — controle falhou, risco ativo |
| **MITIGATE** | Controle mitigador a implementar — risco presente mas parcialmente controlado |
| **ESCALATE** | Escalar para gestor / comitê — decisão requer autorização superior |
| **ACCEPT** | Risco aceito formalmente — dentro dos limites aceitáveis, documentar |
| **MONITOR** | Continuar monitorando — próximo de threshold, sem ação imediata |

---

## 5. Vocabulário de prioridade

| Prioridade | SLA sugerido | Critério |
|---|---|---|
| **URGENTE** | 24–72h | Falha crítica com LGPD trigger ativo |
| **ALTA** | 5–15 dias | Falha com risco operacional relevante |
| **MÉDIA** | 15–30 dias | Risco presente, controle parcial ativo |
| **BAIXA** | Próximo ciclo | Dentro dos parâmetros — monitoramento |

---

## 6. Combinação ISO + LGPD no export

Cada métrica avaliada pelo dashboard gera um objeto de decisão com a seguinte estrutura:

```json
{
  "control": "5.3",
  "metric": "conflicts_critical",
  "value": 12,
  "risk_level": "HIGH",
  "control_failure": true,
  "risk_type": "FRAUDE_ACESSO_INDEVIDO",
  "lgpd_article": "Art. 46º",
  "lgpd_impact": "dados financeiros/pessoais expostos por conflito de função",
  "lgpd_trigger": true,
  "regulatory_risk": "SANCAO_ADMINISTRATIVA",
  "decision": "REMEDIATE",
  "decision_suggested": "REMEDIATE",
  "decision_confirmed": false,
  "priority": "URGENTE",
  "analyst_note": "",
  "evaluated_at": "2026-03-31T00:00:00Z"
}
```

O campo `decision_confirmed: false` indica decisão sugerida aguardando confirmação do analista.  
Após confirmação no dashboard, `decision_confirmed` passa para `true` e o campo `analyst_note` registra a justificativa.

---

## 7. Referências normativas

- **ISO/IEC 27001:2022** — Anexo A: Controles de segurança da informação
- **ISO/IEC 27002:2022** — Guia de implementação dos controles
- **LGPD — Lei 13.709/2018** — Arts. 6º, 46º, 48º, 52º
- **Resolução CD/ANPD nº 4/2023** — Regulamento de dosimetria e aplicação de sanções
- **ISO/IEC 27701:2019** — Extensão de privacidade para sistemas de gestão de segurança

*Este modelo é educacional e representa uma interpretação dos controles ISO com fins de estudo.  
Não substitui análise jurídica ou consultoria especializada em proteção de dados.*

---

## 7. Persistência da decisão no ciclo — cadeia de evidência

Quando o analista confirma uma decisão no dashboard, ela é gravada diretamente no objeto de ciclo em memória, no campo `risk_decisions`. Isso garante que qualquer export posterior — snapshot JSON, histórico ou relatório HTML — carregue a decisão confirmada sem depender de uma sessão ativa.

### Estrutura persistida em `cycle.risk_decisions`

```json
{
  "_persisted_at": "2026-03-31T14:22:00.000Z",
  "engine_version": "2.0",
  "normative_refs": ["ISO/IEC 27001:2022", "LGPD Lei 13.709/2018"],
  "confirmed_count": 8,
  "total_count": 11,
  "findings": [
    {
      "control": "5.3",
      "metric": "conflicts_critical",
      "metric_label": "Conflitos SoD críticos",
      "value": 12,
      "risk_level": "CRITICAL",
      "control_failure": true,
      "risk_type": "FRAUDE_ACESSO_INDEVIDO",
      "lgpd_trigger": true,
      "lgpd_article": "Art. 46º",
      "lgpd_impact": "dados financeiros/pessoais expostos por conflito de função",
      "regulatory_risk": "SANCAO_ADMINISTRATIVA",
      "decision_suggested": "REMEDIATE",
      "decision": "REMEDIATE",
      "decision_confirmed": true,
      "priority": "URGENTE",
      "analyst_note": "Aprovado plano de remediação em reunião do comitê de risco 2026-03-28",
      "evaluated_at": "2026-03-31T14:00:00.000Z",
      "confirmed_at": "2026-03-31T14:22:00.000Z"
    }
  ]
}
```

### Cadeia de evidência — ponta a ponta

```
Extração (SAP/SF/TOTVS/Entra)
        ↓ hash SHA-1 no manifesto
Import no dashboard
        ↓ motor de risco avalia automaticamente
Decisão sugerida (REMEDIATE / ESCALATE / MITIGATE / ACCEPT)
        ↓ analista confirma + justificativa
persistDecisions() → gravada em cycle.risk_decisions
        ↓ incluída em qualquer export subsequente
Export JSON snapshot / histórico / relatório HTML auditor
        ↓ campo risk_decisions.findings[].decision_confirmed = true
Evidência auditável completa — do dado bruto à decisão humana registrada
```

### Restauração ao alternar ciclos

Ao navegar entre ciclos, o dashboard restaura automaticamente as decisões confirmadas do campo `risk_decisions` do ciclo carregado. Decisões anteriores não são perdidas ao trocar de ciclo.

### Campos de rastreabilidade por achado confirmado

| Campo | Tipo | Descrição |
|---|---|---|
| `decision_suggested` | string | Decisão original do motor de risco |
| `decision` | string | Decisão final (analista pode alterar) |
| `decision_confirmed` | boolean | `true` após confirmação explícita |
| `analyst_note` | string | Justificativa obrigatória se decisão foi alterada |
| `evaluated_at` | ISO-8601 | Quando o motor avaliou |
| `confirmed_at` | ISO-8601 | Quando o analista confirmou |
