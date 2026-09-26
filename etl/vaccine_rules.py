"""Motor normativo versionado do PREVNAR.

Objetivo: apoiar vigilância, monitoramento e organização operacional.
Não substitui avaliação clínica individual nem a consulta à norma oficial vigente.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from paths import REF

VACCINE_REGISTRY = REF / "vaccine_registry.json"
NORMATIVE_RULES = REF / "normative_rules.json"
LEGAL_REGISTER = Path(__file__).resolve().parents[1] / "docs" / "legal_register.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def vaccine_registry() -> dict[str, Any]:
    return _load(VACCINE_REGISTRY)


def normative_rules() -> dict[str, Any]:
    return _load(NORMATIVE_RULES)


def legal_register() -> dict[str, Any]:
    return _load(LEGAL_REGISTER)


def get_vaccine(vaccine_id: str) -> dict[str, Any]:
    for row in vaccine_registry().get("vaccines", []):
        if row.get("vaccine_id") == vaccine_id:
            return row
    raise KeyError(f"Vacina não registrada: {vaccine_id}")


def vaccine_codes(vaccine_id: str) -> set[str]:
    return {str(x) for x in get_vaccine(vaccine_id).get("pni_codes", [])}


def special_strategy_codes(
    vaccine_id: str,
    *,
    include_observed_compatibility: bool = True,
) -> set[str]:
    vaccine = get_vaccine(vaccine_id)
    registration = vaccine.get("pni_registration") or {}
    codes = {str(x) for x in registration.get("special_strategy_codes", [])}
    if include_observed_compatibility:
        codes |= {str(x) for x in registration.get("observed_legacy_or_api_codes", [])}
    return codes


def default_monitoring_start(vaccine_id: str) -> date | None:
    raw = (get_vaccine(vaccine_id).get("monitoring") or {}).get("default_data_start")
    return date.fromisoformat(raw) if raw else None


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def rule_is_active(rule: dict[str, Any], on_date: date) -> bool:
    if rule.get("status") != "active":
        return False
    start = _parse_date(rule.get("effective_from"))
    end = _parse_date(rule.get("effective_until"))
    if start and on_date < start:
        return False
    if end and on_date > end:
        return False
    return True


def active_rules(vaccine_id: str, *, on_date: date | None = None) -> list[dict[str, Any]]:
    day = on_date or date.today()
    return [
        row
        for row in normative_rules().get("rules", [])
        if row.get("vaccine_id") == vaccine_id and rule_is_active(row, day)
    ]


def validate_registry_integrity() -> list[str]:
    """Valida referências cruzadas entre vacinas, regras e registro legal."""
    errors: list[str] = []
    vaccines = {
        str(v["vaccine_id"]): v
        for v in vaccine_registry().get("vaccines", [])
        if v.get("vaccine_id")
    }
    rules = normative_rules().get("rules", [])
    legal_ids = {
        str(a["id"])
        for a in legal_register().get("acts", [])
        if a.get("id")
    }

    seen_rules: set[str] = set()
    for rule in rules:
        rid = str(rule.get("rule_id") or "")
        vid = str(rule.get("vaccine_id") or "")
        if not rid:
            errors.append("Regra sem rule_id.")
            continue
        if rid in seen_rules:
            errors.append(f"rule_id duplicado: {rid}")
        seen_rules.add(rid)
        if vid not in vaccines:
            errors.append(f"Regra {rid} referencia vacina ausente: {vid}")
        for act_id in rule.get("normative_acts") or []:
            if str(act_id) not in legal_ids:
                errors.append(f"Regra {rid} referencia ato legal ausente: {act_id}")

    for vid, vaccine in vaccines.items():
        for act_id in vaccine.get("normative_acts") or []:
            if str(act_id) not in legal_ids:
                errors.append(f"Vacina {vid} referencia ato legal ausente: {act_id}")
    return errors


def _history_rule(rule: dict[str, Any], history: str) -> dict[str, Any] | None:
    for item in rule.get("prior_history_rules") or []:
        if item.get("history") == history:
            return item
    return None


def _age_schedule(rule: dict[str, Any], age_months: int) -> dict[str, Any] | None:
    for schedule in rule.get("schedules") or []:
        min_age = schedule.get("min_age_months")
        max_age = schedule.get("max_age_months")
        if min_age is not None and age_months < int(min_age):
            continue
        if max_age is not None and age_months > int(max_age):
            continue
        return schedule
    return None


def _evaluate_rie(
    rule: dict[str, Any],
    *,
    age_months: int,
    condition_ids: set[int],
    pneumococcal_history: str,
) -> dict[str, Any] | None:
    population = rule.get("population") or {}
    eligible_conditions = {int(x) for x in population.get("condition_ids") or []}
    matched = sorted(condition_ids & eligible_conditions)
    if not matched:
        return None
    if age_months < int(population.get("min_age_months") or 0):
        return {
            "rule_id": rule["rule_id"],
            "pathway": "rie_special",
            "eligible": False,
            "reason": "below_minimum_age",
            "matched_condition_ids": matched,
        }

    # CAR-T is explicitly an exception to the generic ≥5y single-dose schedule,
    # but the current structured source does not encode enough detail to automate it safely.
    if 5 in matched:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "rie_special",
            "eligible": True,
            "matched_condition_ids": matched,
            "requires_review": True,
            "recommendation": "clinical_protocol_review",
            "reason": "car_t_exception_not_fully_automated",
        }

    # TCTH: verified exception for patients from 12 months, 3 doses at 2-month intervals.
    if 4 in matched:
        special = next(
            (
                x
                for x in rule.get("special_schedules") or []
                if int(x.get("condition_id") or -1) == 4
            ),
            None,
        )
        if age_months < int((special or {}).get("min_age_months") or 12):
            return {
                "rule_id": rule["rule_id"],
                "pathway": "rie_special",
                "eligible": True,
                "matched_condition_ids": matched,
                "requires_review": True,
                "recommendation": "clinical_protocol_review",
                "reason": "tcth_under_12_months",
            }
        return {
            "rule_id": rule["rule_id"],
            "pathway": "rie_special",
            "eligible": True,
            "matched_condition_ids": matched,
            "requires_review": False,
            "recommendation": "vpc20_schedule",
            "schedule": special,
        }

    # Prior pneumococcal vaccination modifies the RIE transition strategy.
    if pneumococcal_history not in ("none", "unknown"):
        history = _history_rule(rule, pneumococcal_history)
        if history:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "rie_special",
                "eligible": True,
                "matched_condition_ids": matched,
                "requires_review": False,
                "recommendation": history.get("recommendation"),
                "history_rule": history,
            }
        # Pediatric transition schemes are intentionally not collapsed into a guessed rule.
        return {
            "rule_id": rule["rule_id"],
            "pathway": "rie_special",
            "eligible": True,
            "matched_condition_ids": matched,
            "requires_review": True,
            "recommendation": "transition_schedule_review",
            "reason": "history_not_structured_for_automatic_transition",
        }

    schedule = _age_schedule(rule, age_months)
    if not schedule:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "rie_special",
            "eligible": True,
            "matched_condition_ids": matched,
            "requires_review": True,
            "recommendation": "clinical_protocol_review",
            "reason": "no_schedule_for_age",
        }

    return {
        "rule_id": rule["rule_id"],
        "pathway": "rie_special",
        "eligible": True,
        "matched_condition_ids": matched,
        "requires_review": False,
        "recommendation": "vpc20_schedule",
        "schedule": schedule,
    }


def _evaluate_elderly(
    rule: dict[str, Any],
    *,
    age_months: int,
    pneumococcal_history: str,
) -> dict[str, Any] | None:
    population = rule.get("population") or {}
    min_age_years = int(population.get("min_age_years") or 0)
    if age_months < min_age_years * 12:
        return None

    if pneumococcal_history == "unknown":
        return {
            "rule_id": rule["rule_id"],
            "pathway": "elderly_85_plus",
            "eligible": True,
            "requires_review": True,
            "recommendation": "verify_vaccination_history",
        }

    history = _history_rule(rule, pneumococcal_history)
    if not history:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "elderly_85_plus",
            "eligible": True,
            "requires_review": True,
            "recommendation": "verify_vaccination_history",
            "reason": "history_not_recognized",
        }

    return {
        "rule_id": rule["rule_id"],
        "pathway": "elderly_85_plus",
        "eligible": True,
        "requires_review": False,
        "recommendation": history.get("recommendation"),
        "history_rule": history,
        "prescription_required": population.get("prescription_required"),
    }


def evaluate_operational(
    vaccine_id: str,
    *,
    age_months: int,
    condition_ids: list[int] | set[int] | None = None,
    pneumococcal_history: str = "unknown",
    on_date: date | None = None,
) -> dict[str, Any]:
    """Avalia caminhos configurados para suporte operacional.

    Retorna caminhos aplicáveis sem decidir conflitos clínicos entre eles.
    """
    day = on_date or date.today()
    conditions = {int(x) for x in (condition_ids or [])}
    pathways: list[dict[str, Any]] = []

    for rule in active_rules(vaccine_id, on_date=day):
        if rule.get("rule_type") != "eligibility_and_schedule":
            continue
        strategy = (rule.get("population") or {}).get("strategy")
        result: dict[str, Any] | None = None
        if strategy == "rie_special":
            result = _evaluate_rie(
                rule,
                age_months=age_months,
                condition_ids=conditions,
                pneumococcal_history=pneumococcal_history,
            )
        elif strategy == "elderly_85_plus":
            result = _evaluate_elderly(
                rule,
                age_months=age_months,
                pneumococcal_history=pneumococcal_history,
            )
        if result:
            pathways.append(result)

    requires_review = any(bool(x.get("requires_review")) for x in pathways)
    recommendations = {x.get("recommendation") for x in pathways if x.get("recommendation")}
    if len(recommendations) > 1:
        requires_review = True

    return {
        "vaccine_id": vaccine_id,
        "evaluated_on": day.isoformat(),
        "age_months": age_months,
        "condition_ids": sorted(conditions),
        "pneumococcal_history": pneumococcal_history,
        "eligible_by_any_rule": any(bool(x.get("eligible")) for x in pathways),
        "requires_review": requires_review,
        "pathways": pathways,
        "disclaimer": (
            "Suporte operacional e de vigilância; não substitui avaliação clínica "
            "nem a consulta à norma oficial vigente."
        ),
    }
