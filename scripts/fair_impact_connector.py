#!/usr/bin/env python3
"""
fair_impact_connector.py
------------------------
Conector opcional de impacto financeiro para o IAM Control Effectiveness Model.
Reutiliza métricas já existentes do domínio SoD e produz um resumo financeiro.
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FAIRConnectorConfig:
    magnitude_per_event: float = 80000.0
    months_between_events: float = 24.0
    control_cost: float = 20000.0
    control_reduction_pct: float = 90.0


def connect_fair_summary(cycle: Dict[str, Any], cfg: FAIRConnectorConfig | None = None) -> Dict[str, Any]:
    cfg = cfg or FAIRConnectorConfig()
    sod = (cycle.get("controls") or {}).get("sod") or {}
    critical = float(sod.get("conflicts_critical") or 0)
    untreated_pct = float(sod.get("untreated_pct") or 0)
    active_conflicts = critical * (untreated_pct / 100.0)
    frequency = active_conflicts * (12.0 / cfg.months_between_events)
    annual_exposure = frequency * cfg.magnitude_per_event
    residual_exposure = annual_exposure * (1 - cfg.control_reduction_pct / 100.0)
    reduction_value = annual_exposure - residual_exposure
    roi_pct = ((reduction_value - cfg.control_cost) / cfg.control_cost) * 100 if cfg.control_cost else None

    if annual_exposure > 100000:
        decision = "TRATAR COM PRIORIDADE"
    elif annual_exposure > 30000:
        decision = "TRATAR"
    else:
        decision = "MONITORAR"

    return {
        "connector_status": "CONNECTED" if critical > 0 else "NOT_APPLICABLE",
        "source_metric": "5.3",
        "active_conflicts_est": round(active_conflicts, 2),
        "loss_event_frequency_annual": round(frequency, 2),
        "loss_magnitude": round(cfg.magnitude_per_event, 2),
        "annual_exposure": round(annual_exposure, 2),
        "residual_exposure": round(residual_exposure, 2),
        "risk_reduction_value": round(reduction_value, 2),
        "control_cost": round(cfg.control_cost, 2),
        "control_roi_pct": None if roi_pct is None else round(roi_pct, 0),
        "decision_hint": decision,
    }
