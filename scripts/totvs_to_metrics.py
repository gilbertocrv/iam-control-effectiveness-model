#!/usr/bin/env python3
"""
totvs_to_metrics.py
-------------------
Converte exports TOTVS Protheus (SYS_USR + ADS SoD) para o formato
metrics.csv do iam-governance-dashboard.

Uso:
    python scripts/totvs_to_metrics.py \
        --users     samples/totvs/totvs_sys_usr.csv \
        --conflicts samples/totvs/totvs_sod_conflicts.csv \
        --cycle     2026-Q1 \
        --date      2026-03-31 \
        --out       metrics_output.csv

Fontes TOTVS:
  --users     → Relatório SYS_USR + SIGAPBF (Configurador > Segurança > Usuários)
  --conflicts → Query SQL na tabela ADS (rotinas conflitantes por usuário)

Query SQL sugerida para --conflicts (SQL Server / Informix):
    SELECT a.USR_CODE, a.USR_NAME,
           b.ADS_ROTINA AS ROTINA_A, b.ADS_DESC AS DESC_ROTINA_A,
           c.ADS_ROTINA AS ROTINA_B, c.ADS_DESC AS DESC_ROTINA_B,
           'Manual' AS CONFLICT_TYPE,
           CASE WHEN b.ADS_NIVEL = '1' THEN 'Critical' ELSE 'High' END AS SEVERITY
    FROM SYS_USR a
    JOIN SIGAPBF b ON b.USR_CODE = a.USR_CODE AND b.ADS_ROTINA IN ('FINA010','COMP010','RH010')
    JOIN SIGAPBF c ON c.USR_CODE = a.USR_CODE AND c.ADS_ROTINA IN ('FINA030','COMP030','RH030')
    WHERE a.USR_STATUS = '1'

GitHub Actions: ver .github/workflows/convert-metrics.yml
"""

import argparse
import csv
import os
import sys
from datetime import datetime, date

SOURCE = "totvs-protheus-cfg"

INACTIVE_THRESHOLD_DAYS = 90


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


def days_since_totvs(date_str: str) -> int:
    """
    TOTVS usa formato YYYYMMDD no campo USR_DTLAST.
    Aceita também YYYY-MM-DD como fallback.
    """
    if not date_str or date_str.strip() in ("", " ", "0", "00000000"):
        return 9999
    date_str = date_str.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(date_str[:8] if fmt == "%Y%m%d" else date_str, fmt).date()
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


# ── SYS_USR — USERS & GROUPS ─────────────────────────────────────────────────

def process_users(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.15 · access_via_group_pct     (usuários com grupo atribuído)
      5.15 · direct_access_pct        (usuários sem grupo / acesso individual)
      8.2  · inactive_accounts_pct    (USR_DTLAST > 90 dias)
      8.2  · privileged_accounts      (USR_TYPE = 'S' — administradores)
      8.3  · groups_without_owner     (grupos sem USR_OWNER definido)
    """
    if not rows:
        return []

    total    = len(rows)
    # USR_TYPE 'S' = supervisor/admin no Protheus
    privileged = sum(1 for r in rows if r.get("USR_TYPE", "").strip().upper() == "S")
    inactive   = sum(1 for r in rows
                     if days_since_totvs(r.get("USR_DTLAST", "")) > INACTIVE_THRESHOLD_DAYS)
    with_group = sum(1 for r in rows if r.get("USR_GROUP", "").strip() not in ("", "SEM"))
    no_group   = total - with_group

    # Grupos sem owner: USR_OWNER em branco
    # Agrupa por grupo e verifica se algum usuário tem owner definido
    groups: dict[str, bool] = {}
    for r in rows:
        grp = r.get("USR_GROUP", "").strip()
        if not grp:
            continue
        has_owner = bool(r.get("USR_OWNER", "").strip())
        # Se qualquer membro do grupo tiver owner, o grupo tem owner
        groups[grp] = groups.get(grp, False) or has_owner

    groups_without_owner = sum(1 for has_owner in groups.values() if not has_owner)

    print(f"[TOTVS-USR] {total} usuários · {privileged} admins · "
          f"{inactive} inativos >{INACTIVE_THRESHOLD_DAYS}d · "
          f"{groups_without_owner}/{len(groups)} grupos sem owner")

    return [
        metric("5.15", "access_via_group_pct",   pct(with_group, total), "percent", cycle_id, cycle_date, SOURCE),
        metric("5.15", "direct_access_pct",       pct(no_group, total),   "percent", cycle_id, cycle_date, SOURCE),
        metric("8.2",  "privileged_accounts",      privileged,             "count",   cycle_id, cycle_date, SOURCE),
        metric("8.2",  "inactive_accounts_pct",    pct(inactive, total),   "percent", cycle_id, cycle_date, SOURCE),
        metric("8.3",  "groups_without_owner",     groups_without_owner,   "count",   cycle_id, cycle_date, SOURCE),
    ]


# ── ADS — SoD CONFLICTS ───────────────────────────────────────────────────────

def process_conflicts(rows: list[dict], cycle_id: str, cycle_date: str) -> list[dict]:
    """
    Métricas geradas:
      5.3 · conflicts_total
      5.3 · conflicts_critical
      5.3 · conflicts_medium
      5.3 · conflicts_low
      5.3 · untreated_pct      (assume sem mitigação — TOTVS não tem motor nativo)
    """
    if not rows:
        return []

    total    = len(rows)
    critical = sum(1 for r in rows if r.get("SEVERITY", "").strip() in ("Critical",))
    high     = sum(1 for r in rows if r.get("SEVERITY", "").strip() in ("High",))
    medium   = sum(1 for r in rows if r.get("SEVERITY", "").strip() == "Medium")
    low      = sum(1 for r in rows if r.get("SEVERITY", "").strip() == "Low")

    # TOTVS não tem motor de SoD nativo — conflitos identificados via SQL são todos "não tratados"
    # por definição (sem controle mitigador documentado no sistema)
    untreated = total

    print(f"[TOTVS-SOD] {total} conflitos · {critical} críticos · {high} altos · "
          f"{medium} médios · {low} baixos")

    return [
        metric("5.3", "conflicts_total",    total,                            "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "conflicts_critical", critical + high,                  "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "conflicts_medium",   medium,                           "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "conflicts_low",      low,                              "count",   cycle_id, cycle_date, SOURCE),
        metric("5.3", "untreated_pct",      pct(untreated, total),            "percent", cycle_id, cycle_date, SOURCE),
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
        description="Converte exports TOTVS Protheus (SYS_USR + ADS) → metrics.csv"
    )
    parser.add_argument("--users",     help="CSV de usuários SYS_USR")
    parser.add_argument("--conflicts", help="CSV de conflitos SoD (query ADS)")
    parser.add_argument("--cycle",     required=True, help="ID do ciclo, ex: 2026-Q1")
    parser.add_argument("--date",      required=True, help="Data de referência YYYY-MM-DD")
    parser.add_argument("--out",       default="metrics_totvs.csv", help="Arquivo de saída")
    parser.add_argument("--append",    action="store_true", help="Anexar ao arquivo existente")
    parser.add_argument("--inactive-days", type=int, default=90,
                        help="Dias sem login para considerar conta inativa (padrão: 90)")
    args = parser.parse_args()

    global INACTIVE_THRESHOLD_DAYS
    INACTIVE_THRESHOLD_DAYS = args.inactive_days

    all_metrics: list[dict] = []

    if args.users:
        all_metrics += process_users(read_csv(args.users), args.cycle, args.date)
    if args.conflicts:
        all_metrics += process_conflicts(read_csv(args.conflicts), args.cycle, args.date)

    if not all_metrics:
        print("[ERRO] Nenhum arquivo de entrada fornecido ou arquivos vazios.", file=sys.stderr)
        sys.exit(1)

    write_metrics(all_metrics, args.out, append=args.append)
    print(f"[OK] Conversão TOTVS Protheus concluída → {args.out}")


if __name__ == "__main__":
    main()
