#!/usr/bin/env python3
"""
kpi_kri_mapper.py
-----------------
Camada simples para reorganizar métricas do modelo em KPI e KRI.

Uso:
    python scripts/kpi_kri_mapper.py input_cycle.json
"""

import json
import sys

def build_layers(cycle: dict) -> dict:
    controls = cycle.get("controls", {})
    review = controls.get("review", {})
    evidence = controls.get("evidence", {})
    sod = controls.get("sod", {})
    pam = controls.get("pam", {})

    return {
        "kpi": {
            "reviews_completed_pct": review.get("reviews_completed_pct"),
            "avg_resolution_days": sod.get("avg_resolution_days"),
            "decisions_with_evidence_pct": evidence.get("decisions_with_evidence_pct"),
            "exceptions_documented_pct": evidence.get("exceptions_documented_pct"),
        },
        "kri": {
            "conflicts_critical": sod.get("conflicts_critical"),
            "untreated_pct": sod.get("untreated_pct"),
            "mfa_coverage_pct": pam.get("mfa_coverage_pct"),
            "inactive_accounts_pct": pam.get("inactive_accounts_pct"),
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python scripts/kpi_kri_mapper.py input_cycle.json")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    cycle = data[0] if isinstance(data, list) else data
    print(json.dumps(build_layers(cycle), ensure_ascii=False, indent=2))
