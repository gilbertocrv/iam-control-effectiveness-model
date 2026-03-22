#!/usr/bin/env python3
"""
sap_to_metrics.py
-----------------
Converte exports do SAP GRC (ARA + SUIM + EAM) para o formato
metrics.csv do iam-governance-dashboard.

Uso:
    python scripts/sap_to_metrics.py \
        --ara   samples/sap/sap_ara_violations.csv \
        --suim  samples/sap/sap_suim_users.csv \
        --eam   samples/sap/sap_eam_firefighter.csv \
        --cycle 2026-Q1 \
        --date  2026-03-31 \
        --out   metrics_output.csv

GitHub Actions: ver .github/workflows/convert-metrics.yml
"""

import argparse
import csv
import os
import sys
from datetime import datetime, date

SOURCE = "sap-grc"


# ── HELPERS ──────────────────────────────────────────────────────────────────

def read_csv(path: str) -> list[dict]:
    """Lê CSV e retorna lista de dicts. Ignora linhas em branco."""
    if not path or not os.path.exists(path):
        print(f"[AVISO] Arquivo não encontrado: {path}", file=sys.stderr)
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if any(r.values())]


def pct(numerator: int, denominator: int) -> float:
    """Retorna percentual arredondado. Retorna 0 se denominador = 0."""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def days_since(date_str: str) -> int:
    """Calcula dias desde uma data (formatos YYYY-MM-DD ou YYYYMMDD)."""
    if not date_str or date_str.strip() in ("", " "):
        return 9999
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(date_str, fmt).date()
            return (date.today() - d).days
        except ValueError:
            continue
    return 9999


def metric(control: str, name: str, value, unit: str, cycle_id: str,
           cycle_date: str, source: str) -> dict:
    return {
        "control": control,
        "metric": name,
        "value": value,
        "unit": unit,
        "cycle_id": cycle_id,
        "cycle_date": cycle_date,
        "source": source,
    }


# ── ARA — SoD VIOLATIONS ─────────────────────────────────────────────────────

def process_ara(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.3 · conflicts_total
      5.3 · conflicts_critical
      5.3 · conflicts_medium
      5.3 · conflicts_low
      5.3 · untreated_pct
    """
    if not rows:
        return []

    total = len(rows)
    critical = sum(1 for r in rows if r.get("RiskLevel", "").strip() in ("Critical", "High"))
    medium   = sum(1 for r in rows if r.get("RiskLevel", "").strip() == "Medium")
    low      = sum(1 for r in rows if r.get("RiskLevel", "").strip() == "Low")
    mitigated = sum(1 for r in rows if r.get("Status", "").strip().lower() == "mitigated")
    untreated = total - mitigated

    print(f"[ARA] {total} violações · {critical} críticas/altas · {mitigated} mitigadas")

    return [
        metric("5.3", "conflicts_total",    total,              "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "conflicts_critical", critical,           "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "conflicts_medium",   medium,             "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "conflicts_low",      low,                "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "untreated_pct",      pct(untreated, total), "percent", cycle_id, cycle_date, SOURCE),
    ]


# ── SUIM — USERS & PROFILES ──────────────────────────────────────────────────

def process_suim(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.15 · access_via_group_pct
      5.15 · direct_access_pct
      8.2  · privileged_accounts
      8.2  · inactive_accounts_pct
      8.3  · users_multiple_roles_pct
    """
    if not rows:
        return []

    # Agrupa por usuário
    users: dict[str, dict] = {}
    for r in rows:
        uid = r.get("UserID", "").strip()
        if not uid:
            continue
        if uid not in users:
            users[uid] = {
                "type": r.get("UserType", "Dialog"),
                "last_login": r.get("LastLogin", ""),
                "status": r.get("AccountStatus", "Active"),
                "profiles_direct": 0,
                "roles": 0,
                "profile_type": [],
            }
        pt = r.get("ProfileType", "").strip()
        assigned = r.get("AssignedDirectly", "No").strip()
        if assigned.lower() == "yes" and pt == "Profile":
            users[uid]["profiles_direct"] += 1
        if pt == "Role":
            users[uid]["roles"] += 1
        users[uid]["profile_type"].append(pt)

    total_users = len(users)
    direct_access = sum(1 for u in users.values() if u["profiles_direct"] > 0)
    group_access   = total_users - direct_access
    multiple_roles = sum(1 for u in users.values() if u["roles"] > 1)

    # Contas privilegiadas = tipo System/Service OU com SAP_ALL direto
    privileged = sum(1 for u in users.values()
                     if u["type"] in ("System", "Service") or u["profiles_direct"] > 0)

    # Contas inativas: último login > 90 dias
    inactive = sum(1 for u in users.values()
                   if days_since(u["last_login"]) > 90)

    print(f"[SUIM] {total_users} usuários · {direct_access} acesso direto · "
          f"{privileged} privilegiados · {inactive} inativos >90d")

    return [
        metric("5.15", "access_via_group_pct",      pct(group_access, total_users),   "percent", cycle_id, cycle_date, SOURCE),
        metric("5.15", "direct_access_pct",          pct(direct_access, total_users), "percent", cycle_id, cycle_date, SOURCE),
        metric("8.2",  "privileged_accounts",         privileged,                      "count",   cycle_id, cycle_date, SOURCE),
        metric("8.2",  "inactive_accounts_pct",       pct(inactive, total_users),      "percent", cycle_id, cycle_date, SOURCE),
        metric("8.3",  "users_multiple_roles_pct",    pct(multiple_roles, total_users),"percent", cycle_id, cycle_date, SOURCE),
    ]


# ── EAM — FIREFIGHTER LOG ─────────────────────────────────────────────────────

def process_eam(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.33 · decisions_with_evidence_pct  (uso de FF com revisão documentada)
      8.2  · critical_service_principals  (sessões de FF não revisadas = exposição)
    """
    if not rows:
        return []

    total = len(rows)
    reviewed = sum(1 for r in rows if r.get("Reviewed", "No").strip().lower() == "yes")
    unreviewed = total - reviewed

    print(f"[EAM] {total} sessões FF · {reviewed} revisadas · {unreviewed} pendentes")

    return [
        metric("5.33", "decisions_with_evidence_pct", pct(reviewed, total), "percent", cycle_id, cycle_date, SOURCE),
        metric("8.2",  "critical_service_principals",  unreviewed,           "count",   cycle_id, cycle_date, SOURCE),
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
        description="Converte exports SAP GRC (ARA + SUIM + EAM) → metrics.csv"
    )
    parser.add_argument("--ara",   help="CSV de violações ARA (GRAC_REPORTING)")
    parser.add_argument("--suim",  help="CSV de usuários e perfis (SUIM/RSUSR002)")
    parser.add_argument("--eam",   help="CSV de log Firefighter (GRAC_SPM)")
    parser.add_argument("--cycle", required=True, help="ID do ciclo, ex: 2026-Q1")
    parser.add_argument("--date",  required=True, help="Data de referência YYYY-MM-DD")
    parser.add_argument("--out",   default="metrics_sap.csv", help="Arquivo de saída")
    parser.add_argument("--append", action="store_true", help="Anexar ao arquivo existente")
    args = parser.parse_args()

    all_metrics: list[dict] = []

    if args.ara:
        all_metrics += process_ara(read_csv(args.ara), args.cycle, args.date)
    if args.suim:
        all_metrics += process_suim(read_csv(args.suim), args.cycle, args.date)
    if args.eam:
        all_metrics += process_eam(read_csv(args.eam), args.cycle, args.date)

    if not all_metrics:
        print("[ERRO] Nenhum arquivo de entrada fornecido ou arquivos vazios.", file=sys.stderr)
        sys.exit(1)

    write_metrics(all_metrics, args.out, append=args.append)
    print(f"[OK] Conversão SAP GRC concluída → {args.out}")


if __name__ == "__main__":
    main()
