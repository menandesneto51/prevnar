"""Motor normativo versionado do PREVNAR.

Objetivo: apoiar vigilância, monitoramento e organização operacional.
Não substitui avaliação clínica individual nem a consulta à norma oficial vigente.

A entidade canônica é "immunobiologic". Vacinas permanecem suportadas por wrappers
de compatibilidade durante a migração.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from paths import REF

IMMUNOBIOLOGIC_REGISTRY = REF / "immunobiologic_registry.json"
VACCINE_REGISTRY = REF / "vaccine_registry.json"  # compatibility view
NORMATIVE_RULES = REF / "normative_rules.json"
LEGAL_REGISTER = Path(__file__).resolve().parents[1] / "docs" / "legal_register.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def immunobiologic_registry() -> dict[str, Any]:
    return _load(IMMUNOBIOLOGIC_REGISTRY)


def vaccine_registry() -> dict[str, Any]:
    """Compatibilidade: view específica de vacinas durante a migração."""
    return _load(VACCINE_REGISTRY)


def normative_rules() -> dict[str, Any]:
    return _load(NORMATIVE_RULES)


def legal_register() -> dict[str, Any]:
    return _load(LEGAL_REGISTER)


def get_immunobiologic(immunobiologic_id: str) -> dict[str, Any]:
    for row in immunobiologic_registry().get("immunobiologics", []):
        if row.get("immunobiologic_id") == immunobiologic_id:
            return row
    raise KeyError(f"Imunobiológico não registrado: {immunobiologic_id}")


def immunobiologic_codes(immunobiologic_id: str) -> set[str]:
    return {
        str(x)
        for x in get_immunobiologic(immunobiologic_id).get("pni_codes", [])
    }


def get_vaccine(vaccine_id: str) -> dict[str, Any]:
    """Wrapper compatível para consumidores que ainda esperam uma vacina."""
    item = get_immunobiologic(vaccine_id)
    if item.get("type") != "vaccine":
        raise KeyError(f"Imunobiológico não é vacina: {vaccine_id}")
    return item


def vaccine_codes(vaccine_id: str) -> set[str]:
    return immunobiologic_codes(vaccine_id)


def special_strategy_codes(
    vaccine_id: str,
    *,
    include_observed_compatibility: bool = True,
) -> set[str]:
    vaccine = get_vaccine(vaccine_id)
    registration = vaccine.get("pni_registration") or {}
    codes = {str(x) for x in registration.get("special_strategy_codes", [])}
    if include_observed_compatibility:
        codes |= {
            str(x)
            for x in registration.get("observed_legacy_or_api_codes", [])
        }
    return codes


def default_monitoring_start(immunobiologic_id: str) -> date | None:
    raw = (
        get_immunobiologic(immunobiologic_id).get("monitoring") or {}
    ).get("default_data_start")
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


def _rule_immunobiologic_id(rule: dict[str, Any]) -> str:
    return str(
        rule.get("immunobiologic_id")
        or rule.get("vaccine_id")
        or ""
    )


def active_rules(
    immunobiologic_id: str,
    *,
    on_date: date | None = None,
) -> list[dict[str, Any]]:
    day = on_date or date.today()
    return [
        row
        for row in normative_rules().get("rules", [])
        if _rule_immunobiologic_id(row) == immunobiologic_id
        and rule_is_active(row, day)
    ]


def validate_registry_integrity() -> list[str]:
    """Valida referências entre imunobiológicos, regras e registro legal."""
    errors: list[str] = []

    immunobiologics = {
        str(v["immunobiologic_id"]): v
        for v in immunobiologic_registry().get("immunobiologics", [])
        if v.get("immunobiologic_id")
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
        iid = _rule_immunobiologic_id(rule)
        if not rid:
            errors.append("Regra sem rule_id.")
            continue
        if rid in seen_rules:
            errors.append(f"rule_id duplicado: {rid}")
        seen_rules.add(rid)

        if not iid:
            errors.append(f"Regra {rid} sem immunobiologic_id/vaccine_id.")
        elif iid not in immunobiologics:
            errors.append(
                f"Regra {rid} referencia imunobiológico ausente: {iid}"
            )

        for act_id in rule.get("normative_acts") or []:
            if str(act_id) not in legal_ids:
                errors.append(
                    f"Regra {rid} referencia ato legal ausente: {act_id}"
                )

    for iid, item in immunobiologics.items():
        item_type = item.get("type")
        if item_type not in {
            "vaccine",
            "monoclonal_antibody",
            "immunoglobulin",
            "other",
        }:
            errors.append(
                f"Imunobiológico {iid} possui type inválido: {item_type}"
            )
        for act_id in item.get("normative_acts") or []:
            if str(act_id) not in legal_ids:
                errors.append(
                    f"Imunobiológico {iid} referencia ato legal ausente: {act_id}"
                )

    # Durante a migração, toda vacina da view legada precisa existir na camada canônica.
    for vaccine in vaccine_registry().get("vaccines", []):
        vid = str(vaccine.get("vaccine_id") or "")
        if not vid:
            errors.append("Vacina sem vaccine_id no registry de compatibilidade.")
            continue
        canonical = immunobiologics.get(vid)
        if not canonical:
            errors.append(
                f"Vacina de compatibilidade {vid} ausente no immunobiologic registry."
            )
            continue
        if canonical.get("type") != "vaccine":
            errors.append(
                f"Compatibilidade inválida: {vid} não possui type=vaccine."
            )

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
    eligible_conditions = {
        int(x) for x in population.get("condition_ids") or []
    }
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


def _evaluate_maternal_rsv(
    rule: dict[str, Any],
    *,
    gestational_age_weeks: float | None,
    already_administered_this_pregnancy: bool | None,
) -> dict[str, Any]:
    population = rule.get("population") or {}
    min_weeks = float(population.get("min_gestational_age_weeks") or 28)

    if already_administered_this_pregnancy is True:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "maternal_rsv",
            "eligible": False,
            "requires_review": False,
            "recommendation": "do_not_repeat_routine_dose",
            "reason": (
                "dose_already_administered_this_pregnancy"
                if gestational_age_weeks is None or gestational_age_weeks >= min_weeks
                else "early_dose_already_administered_monitor_no_repeat"
            ),
        }
    if gestational_age_weeks is None:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "maternal_rsv",
            "eligible": False,
            "requires_review": True,
            "recommendation": "verify_gestational_age",
        }
    if gestational_age_weeks < min_weeks:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "maternal_rsv",
            "eligible": False,
            "requires_review": False,
            "reason": "below_minimum_gestational_age",
        }
    if already_administered_this_pregnancy is None:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "maternal_rsv",
            "eligible": True,
            "requires_review": True,
            "recommendation": "verify_dose_history_this_pregnancy",
        }
    return {
        "rule_id": rule["rule_id"],
        "pathway": "maternal_rsv",
        "eligible": True,
        "requires_review": False,
        "recommendation": "one_dose_vvsr_this_pregnancy",
        "schedule": rule.get("schedule"),
    }


def _evaluate_nirsevimab(
    rule: dict[str, Any],
    *,
    age_months: int,
    birth_gestational_age_days: int | None,
    eligible_comorbidity: bool | None,
    weight_kg: float | None,
    vsr_season_number: int | None,
    in_vsr_season: bool | None,
) -> dict[str, Any]:
    population = rule.get("population") or {}
    prematurity_limit = int(population.get("premature_max_gestational_age_days") or 258)
    premature_age_limit = int(population.get("premature_max_age_months_exclusive") or 6)
    comorbidity_age_limit = int(population.get("comorbidity_max_age_months_exclusive") or 24)

    premature = (
        birth_gestational_age_days is not None
        and birth_gestational_age_days <= prematurity_limit
        and age_months < premature_age_limit
    )
    comorbidity_eligible = bool(eligible_comorbidity) and age_months < comorbidity_age_limit

    if not premature and not comorbidity_eligible:
        if birth_gestational_age_days is None and eligible_comorbidity is None:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "pediatric_rsv_passive",
                "eligible": False,
                "requires_review": True,
                "recommendation": "verify_prematurity_or_comorbidity",
            }
        return {
            "rule_id": rule["rule_id"],
            "pathway": "pediatric_rsv_passive",
            "eligible": False,
            "requires_review": False,
            "reason": "eligibility_criteria_not_met",
        }

    # Prematuros elegíveis: estratégia ao longo de todo o ano.
    # Comorbidade sem prematuridade elegível: restrita à sazonalidade do VSR.
    if not premature and comorbidity_eligible and in_vsr_season is not True:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "pediatric_rsv_passive",
            "eligible": True,
            "requires_review": True,
            "recommendation": "review_outside_or_unknown_vsr_season",
            "reason": "comorbidity_path_requires_vsr_season",
        }

    if vsr_season_number is None:
        # Para prematuros na primeira exposição, peso resolve a dose; a numeração
        # sazonal só é indispensável para o caminho de segunda sazonalidade.
        if not premature:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "pediatric_rsv_passive",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_vsr_season_number",
            }
        vsr_season_number = 1

    dosing = rule.get("dosing") or []
    if vsr_season_number == 1:
        if weight_kg is None:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "pediatric_rsv_passive",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_weight",
            }
        dose = next(
            (
                d for d in dosing
                if d.get("season_number") == 1
                and (
                    (
                        d.get("weight_kg_max_exclusive") is not None
                        and weight_kg < float(d["weight_kg_max_exclusive"])
                    )
                    or (
                        d.get("weight_kg_min") is not None
                        and weight_kg >= float(d["weight_kg_min"])
                    )
                )
            ),
            None,
        )
        if dose:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "pediatric_rsv_passive",
                "eligible": True,
                "requires_review": False,
                "recommendation": "nirsevimab_single_dose",
                "dose": dose,
            }

    if vsr_season_number >= 2 and comorbidity_eligible:
        dose = next(
            (
                d for d in dosing
                if int(d.get("season_number_min") or 999) <= vsr_season_number
                and d.get("eligible_comorbidity_required")
            ),
            None,
        )
        if dose:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "pediatric_rsv_passive",
                "eligible": True,
                "requires_review": False,
                "recommendation": "nirsevimab_seasonal_dose",
                "dose": dose,
            }

    return {
        "rule_id": rule["rule_id"],
        "pathway": "pediatric_rsv_passive",
        "eligible": True,
        "requires_review": True,
        "recommendation": "clinical_protocol_review",
        "reason": "dose_rule_not_resolved",
    }


def evaluate_operational(
    immunobiologic_id: str,
    *,
    age_months: int,
    condition_ids: list[int] | set[int] | None = None,
    pneumococcal_history: str = "unknown",
    gestational_age_weeks: float | None = None,
    already_administered_this_pregnancy: bool | None = None,
    birth_gestational_age_days: int | None = None,
    eligible_comorbidity: bool | None = None,
    weight_kg: float | None = None,
    vsr_season_number: int | None = None,
    in_vsr_season: bool | None = None,
    on_date: date | None = None,
) -> dict[str, Any]:
    """Avalia caminhos configurados para suporte operacional.

    Regras em draft/onboarding nunca são retornadas por active_rules().
    """
    day = on_date or date.today()
    conditions = {int(x) for x in (condition_ids or [])}
    item = get_immunobiologic(immunobiologic_id)
    pathways: list[dict[str, Any]] = []

    for rule in active_rules(immunobiologic_id, on_date=day):
        if rule.get("rule_type") != "eligibility_and_schedule":
            continue
        strategy = (rule.get("population") or {}).get("strategy")
        result: dict[str, Any] | None = None

        # Atualmente somente o domínio pneumocócico está automatizado.
        # Novos imunobiológicos devem ganhar evaluators explícitos após onboarding.
        if immunobiologic_id == "vpc20" and strategy == "rie_special":
            result = _evaluate_rie(
                rule,
                age_months=age_months,
                condition_ids=conditions,
                pneumococcal_history=pneumococcal_history,
            )
        elif immunobiologic_id == "vpc20" and strategy == "elderly_85_plus":
            result = _evaluate_elderly(
                rule,
                age_months=age_months,
                pneumococcal_history=pneumococcal_history,
            )
        elif immunobiologic_id == "vvsr_materna" and strategy == "maternal_rsv":
            result = _evaluate_maternal_rsv(
                rule,
                gestational_age_weeks=gestational_age_weeks,
                already_administered_this_pregnancy=already_administered_this_pregnancy,
            )
        elif immunobiologic_id == "nirsevimab" and strategy == "pediatric_rsv_passive":
            result = _evaluate_nirsevimab(
                rule,
                age_months=age_months,
                birth_gestational_age_days=birth_gestational_age_days,
                eligible_comorbidity=eligible_comorbidity,
                weight_kg=weight_kg,
                vsr_season_number=vsr_season_number,
                in_vsr_season=in_vsr_season,
            )

        if result:
            pathways.append(result)

    requires_review = any(
        bool(x.get("requires_review")) for x in pathways
    )
    recommendations = {
        x.get("recommendation")
        for x in pathways
        if x.get("recommendation")
    }
    if len(recommendations) > 1:
        requires_review = True

    payload = {
        "immunobiologic_id": immunobiologic_id,
        "immunobiologic_type": item.get("type"),
        "evaluated_on": day.isoformat(),
        "age_months": age_months,
        "condition_ids": sorted(conditions),
        "eligible_by_any_rule": any(
            bool(x.get("eligible")) for x in pathways
        ),
        "requires_review": requires_review,
        "pathways": pathways,
        "disclaimer": (
            "Suporte operacional e de vigilância; não substitui avaliação clínica "
            "nem a consulta à norma oficial vigente."
        ),
    }
    if item.get("type") == "vaccine":
        payload["vaccine_id"] = immunobiologic_id
    if immunobiologic_id == "vpc20":
        payload["pneumococcal_history"] = pneumococcal_history
    return payload
