"""Alertas operacionais para transição de apresentações covid-19.

Entrada agregada; não contém dados individuais.
"""
from __future__ import annotations

from datetime import date
from typing import Any


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, result)


def evaluate_inventory_row(
    row: dict[str, Any],
    *,
    expiry_attention_days: int = 60,
    expiry_critical_days: int = 30,
    high_stock_days: int = 90,
    loss_attention_pct: float = 5.0,
) -> dict[str, Any]:
    ref = date.fromisoformat(str(row["reference_date"]))
    expiry = date.fromisoformat(str(row["expiry_date"]))
    stock = _safe_int(row.get("stock_available_doses"))
    administered = _safe_int(row.get("doses_administered_30d"))
    physical = _safe_int(row.get("physical_losses_30d"))
    technical = _safe_int(row.get("technical_losses_30d"))
    capacity = row.get("storage_capacity_doses")
    requested = row.get("requested_doses_next_cycle")

    days_to_expiry = (expiry - ref).days
    daily_consumption = administered / 30 if administered > 0 else 0.0
    days_of_stock = stock / daily_consumption if daily_consumption > 0 else None
    denominator = administered + physical + technical
    loss_rate_pct = (
        100 * (physical + technical) / denominator
        if denominator > 0
        else 0.0
    )

    alerts: list[dict[str, Any]] = []

    if stock > 0 and days_to_expiry <= expiry_critical_days:
        alerts.append({
            "alert_id":"lot_expiry_risk",
            "severity":"critical",
            "reason":f"Lote com {stock} doses e {days_to_expiry} dias até o vencimento.",
        })
    elif stock > 0 and days_to_expiry <= expiry_attention_days:
        alerts.append({
            "alert_id":"lot_expiry_risk",
            "severity":"attention",
            "reason":f"Lote com {stock} doses e {days_to_expiry} dias até o vencimento.",
        })

    if stock > 0 and administered == 0:
        alerts.append({
            "alert_id":"high_stock_low_consumption",
            "severity":"attention",
            "reason":"Estoque positivo sem consumo registrado nos últimos 30 dias.",
        })
    elif days_of_stock is not None and days_of_stock > high_stock_days:
        alerts.append({
            "alert_id":"high_stock_low_consumption",
            "severity":"attention",
            "reason":f"Estoque estimado para {days_of_stock:.1f} dias no ritmo recente.",
        })

    if loss_rate_pct >= loss_attention_pct:
        alerts.append({
            "alert_id":"loss_rate_increase",
            "severity":"attention",
            "reason":f"Taxa de perdas de {loss_rate_pct:.1f}% nos últimos 30 dias.",
        })

    if capacity is not None:
        cap = _safe_int(capacity)
        if stock > cap > 0:
            alerts.append({
                "alert_id":"cold_chain_capacity_constraint",
                "severity":"critical",
                "reason":f"Estoque ({stock}) excede capacidade informada ({cap}).",
            })

    if requested is not None:
        req = _safe_int(requested)
        expected_30d = max(administered, 1)
        if req > expected_30d * 2:
            alerts.append({
                "alert_id":"request_above_consumption_capacity",
                "severity":"attention",
                "reason":(
                    f"Solicitação ({req}) supera 2x o consumo recente "
                    f"({administered}) sem justificativa estruturada."
                ),
            })

    rank = {"critical": 0, "attention": 1, "info": 2}
    alerts.sort(key=lambda x: (rank.get(x["severity"], 99), x["alert_id"]))

    return {
        "territory_code": row.get("territory_code"),
        "facility_cnes": row.get("facility_cnes"),
        "product_variant_id": row.get("product_variant_id"),
        "lot": row.get("lot"),
        "reference_date": ref.isoformat(),
        "expiry_date": expiry.isoformat(),
        "metrics": {
            "days_to_expiry": days_to_expiry,
            "days_of_stock_at_recent_consumption": (
                round(days_of_stock, 1) if days_of_stock is not None else None
            ),
            "loss_rate_30d_pct": round(loss_rate_pct, 2),
        },
        "alerts": alerts,
        "has_critical_alert": any(x["severity"] == "critical" for x in alerts),
        "interpretation": (
            "Alertas operacionais de estoque/transição. Não representam recomendação clínica "
            "nem substituem validação logística institucional."
        ),
    }
