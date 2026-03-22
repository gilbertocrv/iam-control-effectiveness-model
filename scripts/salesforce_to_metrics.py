#!/usr/bin/env python3
"""
salesforce_to_metrics.py
------------------------
Converte exports Salesforce (Users + Audit Trail) para o formato
metrics.csv do iam-governance-dashboard.

Uso:
    python scripts/salesforce_to_metrics.py \
        --users  samples/salesforce/sf_users_profiles.csv \
        --audit  samples/salesforce/sf_audit_trail.csv \
        --cycle  2026-Q1 \
        --date   2026-03-31 \
        --out    metrics_output.csv

Fontes Salesforce:
  --users  → Relatório "Users with Profiles and Permission Sets"
  --audit  → "Setup Audit Trail" (Admin > Setup > Security > View Setup Audit Trail)

GitHub Actions: ver .github/workflows/convert-metrics.yml
"""

import argparse
import csv
import os
import sys
from datetime import datetime, date

SOURCE = "salesforce-audit"


# ── HELPERS ──────────────────────────────────────────────────────────────────

def read_csv(path: str) -> list[dict]:
    if not path or not os.path.exists(path):
        print(f"[AVISO] Arquivo não encontrado: {path}", file=sys.stderr)
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if any(r.values())]


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def days_since(date_str: str) -> int:
    if not date_str or date_str.strip() in ("", " "):
        return 9999
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%d/%m/%Y", "%m/%d/%Y"):
        try:
            d = datetime.strptime(date_str[:10], fmt[:10]).date()
            return (date.today() - d).days
        except ValueError:
            continue
    return 9999


def metric(control: str, name: str, value, unit: str,
           cycle_id: str, cycle_date: str, source: str) -> dict:
    return {
        "control": control, "metric": name, "value": value,
        "unit": unit, "cycle_id": cycle_id,
        "cycle_date": cycle_date, "source": source,
    }


# ── USERS — PROFILES & PERMISSION SETS ───────────────────────────────────────

def process_users(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.15 · access_via_group_pct       (usuários com perfil padrão vs sys-admin direto)
      5.15 · direct_access_pct          (inverso)
      8.2  · privileged_accounts        (System Administrator ativos)
      8.2  · mfa_coverage_pct           (MfaEnabled = true entre ativos)
      8.2  · inactive_accounts_pct      (IsActive=true mas sem login >90d)
      8.3  · users_multiple_roles_pct   (PermissionSetCount > 1)
    """
    if not rows:
        return []

    active = [r for r in rows if r.get("IsActive", "").lower() == "true"]
    total  = len(active)

    privileged = sum(1 for r in active if "administrator" in r.get("ProfileName","").lower())
    mfa_on     = sum(1 for r in active if r.get("MfaEnabled", "").lower() == "true")
    inactive   = sum(1 for r in active if days_since(r.get("LastLoginDate", "")) > 90)
    multi_perm = sum(1 for r in active if int(r.get("PermissionSetCount", 0) or 0) > 1)

    # "Acesso via grupo" = usuário com perfil padrão (não sys-admin nem custom direto)
    via_group = total - privileged
    direct    = privileged  # sys-admin tratado como acesso direto a privilégio

    print(f"[SF-USERS] {total} ativos · {privileged} admins · "
          f"{mfa_on} MFA · {inactive} inativos >90d · {multi_perm} multi-permset")

    return [
        metric("5.15", "access_via_group_pct",   pct(via_group, total),  "percent", cycle_id, cycle_date, SOURCE),
        metric("5.15", "direct_access_pct",       pct(direct, total),     "percent", cycle_id, cycle_date, SOURCE),
        metric("8.2",  "privileged_accounts",      privileged,             "count",   cycle_id, cycle_date, SOURCE),
        metric("8.2",  "mfa_coverage_pct",         pct(mfa_on, total),     "percent", cycle_id, cycle_date, SOURCE),
        metric("8.2",  "inactive_accounts_pct",    pct(inactive, total),   "percent", cycle_id, cycle_date, SOURCE),
        metric("8.3",  "users_multiple_roles_pct", pct(multi_perm, total), "percent", cycle_id, cycle_date, SOURCE),
    ]


# ── AUDIT TRAIL ───────────────────────────────────────────────────────────────

def process_audit(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.33 · decisions_with_evidence_pct   (alterações com TicketID / total)
      5.33 · exceptions_documented_pct     (ações críticas com ticket)
    """
    if not rows:
        return []

    total = len(rows)

    # Considera "com evidência" se tiver TicketID preenchido
    with_ticket = sum(1 for r in rows
                      if r.get("TicketID", "").strip() not in ("", "—", "-"))

    # Ações críticas = modificação de perfil, permissão ou política de segurança
    critical_actions = {"userModified", "permSetAssigned", "permSetRevoked",
                        "profileCreated", "mfaPolicyModified", "sessionSettingsModified",
                        "passwordPolicyModified"}
    critical_rows = [r for r in rows if r.get("Action", "").strip() in critical_actions]
    critical_with_ticket = sum(1 for r in critical_rows
                               if r.get("TicketID", "").strip() not in ("", "—", "-"))

    print(f"[SF-AUDIT] {total} entradas · {with_ticket} com ticket · "
          f"{len(critical_rows)} críticas · {critical_with_ticket} críticas com ticket")

    return [
        metric("5.33", "decisions_with_evidence_pct",
               pct(with_ticket, total),                         "percent", cycle_id, cycle_date, SOURCE),
        metric("5.33", "exceptions_documented_pct",
               pct(critical_with_ticket, max(len(critical_rows), 1)), "percent", cycle_id, cycle_date, SOURCE),
    ]


# ── WRITER ────────────────────────────────────────────────────────────────────

FIELDNAMES = ["control", "metric", "value", "unit", "cycle_id", "cycle_date", "source"]


def write_metrics(metrics: list[dict], out_path: str, append: bool = False) -> None:
    mode = "a" if append and os.path.exists(out_path) else "w"
    with open(out_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if mode == "w":
            writer.writeheader()
        writer.writerows(metrics)
    print(f"[OUT] {len(metrics)} métricas → {out_path} (modo: {'append' if mode == 'a' else 'novo'})")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte exports Salesforce (Users + Audit Trail) → metrics.csv"
    )
    parser.add_argument("--users",  help="CSV de usuários e perfis")
    parser.add_argument("--audit",  help="CSV do Setup Audit Trail")
    parser.add_argument("--cycle",  required=True, help="ID do ciclo, ex: 2026-Q1")
    parser.add_argument("--date",   required=True, help="Data de referência YYYY-MM-DD")
    parser.add_argument("--out",    default="metrics_salesforce.csv", help="Arquivo de saída")
    parser.add_argument("--append", action="store_true", help="Anexar ao arquivo existente")
    args = parser.parse_args()

    all_metrics: list[dict] = []

    if args.users:
        all_metrics += process_users(read_csv(args.users), args.cycle, args.date)
    if args.audit:
        all_metrics += process_audit(read_csv(args.audit), args.cycle, args.date)

    if not all_metrics:
        print("[ERRO] Nenhum arquivo de entrada fornecido ou arquivos vazios.", file=sys.stderr)
        sys.exit(1)

    write_metrics(all_metrics, args.out, append=args.append)
    print(f"[OK] Conversão Salesforce concluída → {args.out}")


if __name__ == "__main__":
    main()
