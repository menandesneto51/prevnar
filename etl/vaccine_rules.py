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


def geographic_scope_applies(
    rule: dict[str, Any],
    geographic_context: dict[str, Any] | None = None,
) -> bool:
    scope = rule.get("geographic_scope") or {"type": "national", "codes": ["BR"]}
    scope_type = str(scope.get("type") or "national")
    codes = {str(x) for x in (scope.get("codes") or [])}

    if scope_type == "national":
        return True
    if not geographic_context:
        return False

    if scope_type == "state":
        candidates = {
            str(geographic_context.get("state") or ""),
            str(geographic_context.get("uf") or ""),
            str(geographic_context.get("state_code") or ""),
        }
        return bool(codes & {x for x in candidates if x})

    if scope_type == "municipality":
        candidates = {
            str(geographic_context.get("municipality") or ""),
            str(geographic_context.get("municipality_code") or ""),
            str(geographic_context.get("ibge_municipality_code") or ""),
        }
        return bool(codes & {x for x in candidates if x})

    if scope_type == "facility":
        candidates = {
            str(geographic_context.get("facility") or ""),
            str(geographic_context.get("cnes") or ""),
        }
        return bool(codes & {x for x in candidates if x})

    if scope_type == "polygon":
        polygon_ids = {
            str(x)
            for x in (geographic_context.get("polygon_ids") or [])
            if str(x)
        }
        return bool(codes & polygon_ids)

    return False


def active_rules(
    immunobiologic_id: str,
    *,
    on_date: date | None = None,
    geographic_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    day = on_date or date.today()
    return [
        row
        for row in normative_rules().get("rules", [])
        if _rule_immunobiologic_id(row) == immunobiologic_id
        and rule_is_active(row, day)
        and geographic_scope_applies(row, geographic_context)
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

    allowed_contexts = set(normative_rules().get("allowed_rule_contexts") or [])
    allowed_scope_types = set(
        normative_rules().get("allowed_geographic_scope_types") or []
    )

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

        context = str(rule.get("rule_context") or "")
        if not context:
            errors.append(f"Regra {rid} sem rule_context.")
        elif allowed_contexts and context not in allowed_contexts:
            errors.append(
                f"Regra {rid} possui rule_context inválido: {context}"
            )

        scope = rule.get("geographic_scope")
        if not isinstance(scope, dict):
            errors.append(f"Regra {rid} sem geographic_scope.")
        else:
            scope_type = str(scope.get("type") or "")
            codes = scope.get("codes")
            if not scope_type:
                errors.append(f"Regra {rid} sem geographic_scope.type.")
            elif allowed_scope_types and scope_type not in allowed_scope_types:
                errors.append(
                    f"Regra {rid} possui geographic_scope.type inválido: "
                    f"{scope_type}"
                )
            if scope_type != "national" and not codes:
                errors.append(
                    f"Regra {rid} com escopo {scope_type} sem códigos/território."
                )
            if scope_type == "national" and codes not in (["BR"], None):
                errors.append(
                    f"Regra {rid} nacional deve usar codes=['BR'] ou null."
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


def _evaluate_menacwy(
    rule: dict[str, Any],
    *,
    age_months: int,
    menc_primary_complete: bool | None,
    days_since_last_menc: int | None,
    menacwy_child_booster_received: bool | None,
    menacwy_adolescent_dose_received: bool | None,
) -> dict[str, Any] | None:
    child = rule.get("child_booster") or {}
    child_min = int(child.get("min_age_months") or 12)
    child_max = int(child.get("max_age_months") or 59)

    if child_min <= age_months <= child_max:
        if menacwy_child_booster_received is True:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_child_booster",
                "eligible": False,
                "requires_review": False,
                "recommendation": "routine_booster_already_received",
            }
        if menc_primary_complete is None:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_child_booster",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_menc_primary_series",
            }
        if not menc_primary_complete:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_child_booster",
                "eligible": True,
                "requires_review": True,
                "recommendation": "complete_or_review_meningococcal_primary_series",
            }
        min_interval = int(child.get("min_interval_after_menc_days") or 60)
        if days_since_last_menc is None:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_child_booster",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_interval_after_last_menc",
                "min_interval_days": min_interval,
            }
        if days_since_last_menc < min_interval:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_child_booster",
                "eligible": True,
                "requires_review": False,
                "recommendation": "defer_until_minimum_interval",
                "min_interval_days": min_interval,
            }
        return {
            "rule_id": rule["rule_id"],
            "pathway": "menacwy_child_booster",
            "eligible": True,
            "requires_review": False,
            "recommendation": "one_menacwy_booster",
            "schedule": child,
        }

    adolescent = rule.get("adolescent") or {}
    adolescent_min = int(adolescent.get("min_age_months") or 132)
    adolescent_max = int(adolescent.get("max_age_months") or 179)
    if adolescent_min <= age_months <= adolescent_max:
        if menacwy_adolescent_dose_received is None:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_adolescent",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_adolescent_menacwy_history",
            }
        if menacwy_adolescent_dose_received:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "menacwy_adolescent",
                "eligible": False,
                "requires_review": False,
                "recommendation": "adolescent_dose_already_received",
            }
        return {
            "rule_id": rule["rule_id"],
            "pathway": "menacwy_adolescent",
            "eligible": True,
            "requires_review": False,
            "recommendation": "one_menacwy_dose",
            "schedule": adolescent,
        }

    return None


def _yellow_fever_history_rule(
    rule: dict[str, Any],
    history: str,
) -> dict[str, Any] | None:
    for item in rule.get("history_rules") or []:
        if item.get("history") == history:
            return item
    return None


def _evaluate_yellow_fever(
    rule: dict[str, Any],
    *,
    age_months: int,
    yellow_fever_history: str,
    days_since_last_yellow_fever_dose: int | None,
) -> dict[str, Any] | None:
    if age_months < 6:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "yellow_fever_routine",
            "eligible": False,
            "requires_review": False,
            "reason": "below_routine_and_exception_age",
        }

    if 6 <= age_months <= 8:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "yellow_fever_exception_6_8_months",
            "eligible": True,
            "requires_review": True,
            "recommendation": "risk_benefit_review_for_exceptional_dose_zero",
        }

    # Pessoas >=60 anos: decisão depende de avaliação individual de risco-benefício.
    if age_months >= 60 * 12:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "yellow_fever_older_adult",
            "eligible": True,
            "requires_review": True,
            "recommendation": "individual_risk_benefit_review",
        }

    # Faixa pediátrica do calendário: 9 meses a 4a11m29d.
    if 9 <= age_months <= 59:
        schedule = rule.get("pediatric_schedule") or {}
        if yellow_fever_history == "unknown":
            return {
                "rule_id": rule["rule_id"],
                "pathway": "yellow_fever_pediatric",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_yellow_fever_history",
                "schedule": schedule,
            }
        if yellow_fever_history == "none":
            return {
                "rule_id": rule["rule_id"],
                "pathway": "yellow_fever_pediatric",
                "eligible": True,
                "requires_review": False,
                "recommendation": "start_or_catch_up_two_dose_pediatric_schedule",
                "doses_remaining": 2,
                "schedule": schedule,
                "note": (
                    "Administrar a dose indicada e completar o esquema pediátrico "
                    "com reforço aos 4 anos, respeitando intervalo mínimo de 30 dias. "
                    "Se a criança já estiver com 4 anos, o reforço deve respeitar "
                    "o intervalo mínimo após a primeira dose."
                ),
            }
        if yellow_fever_history == "two_doses_before_5":
            return {
                "rule_id": rule["rule_id"],
                "pathway": "yellow_fever_pediatric",
                "eligible": False,
                "requires_review": False,
                "recommendation": "complete_no_more_doses",
            }
        if yellow_fever_history == "one_dose_before_5":
            booster_age = int(schedule.get("booster_age_months") or 48)
            if age_months < booster_age:
                return {
                    "rule_id": rule["rule_id"],
                    "pathway": "yellow_fever_pediatric",
                    "eligible": False,
                    "requires_review": False,
                    "recommendation": "await_routine_booster_age",
                    "booster_age_months": booster_age,
                }
            min_interval = int(schedule.get("min_interval_days") or 30)
            if days_since_last_yellow_fever_dose is None:
                return {
                    "rule_id": rule["rule_id"],
                    "pathway": "yellow_fever_pediatric",
                    "eligible": True,
                    "requires_review": True,
                    "recommendation": "verify_interval_for_booster",
                    "min_interval_days": min_interval,
                }
            if days_since_last_yellow_fever_dose < min_interval:
                return {
                    "rule_id": rule["rule_id"],
                    "pathway": "yellow_fever_pediatric",
                    "eligible": True,
                    "requires_review": False,
                    "recommendation": "defer_until_minimum_interval",
                    "min_interval_days": min_interval,
                }
            return {
                "rule_id": rule["rule_id"],
                "pathway": "yellow_fever_pediatric",
                "eligible": True,
                "requires_review": False,
                "recommendation": "one_standard_booster",
            }

        return {
            "rule_id": rule["rule_id"],
            "pathway": "yellow_fever_pediatric",
            "eligible": True,
            "requires_review": True,
            "recommendation": "history_not_supported_for_pediatric_auto_rule",
        }

    # 5 a 59 anos: histórico define diretamente a recomendação nacional.
    if 60 <= age_months < 60 * 12:
        if yellow_fever_history == "unknown":
            return {
                "rule_id": rule["rule_id"],
                "pathway": "yellow_fever_age_5_59",
                "eligible": True,
                "requires_review": True,
                "recommendation": "verify_yellow_fever_history",
            }

        lookup_history = (
            "none_age_5_to_59"
            if yellow_fever_history == "none"
            else yellow_fever_history
        )
        history_rule = _yellow_fever_history_rule(rule, lookup_history)
        if not history_rule:
            return {
                "rule_id": rule["rule_id"],
                "pathway": "yellow_fever_age_5_59",
                "eligible": True,
                "requires_review": True,
                "recommendation": "history_not_recognized",
            }

        recommendation = history_rule.get("recommendation")
        min_interval = history_rule.get("min_interval_days")
        if recommendation == "one_booster" and min_interval:
            if days_since_last_yellow_fever_dose is None:
                return {
                    "rule_id": rule["rule_id"],
                    "pathway": "yellow_fever_age_5_59",
                    "eligible": True,
                    "requires_review": True,
                    "recommendation": "verify_interval_for_booster",
                    "min_interval_days": min_interval,
                }
            if days_since_last_yellow_fever_dose < int(min_interval):
                return {
                    "rule_id": rule["rule_id"],
                    "pathway": "yellow_fever_age_5_59",
                    "eligible": True,
                    "requires_review": False,
                    "recommendation": "defer_until_minimum_interval",
                    "min_interval_days": min_interval,
                }

        eligible = recommendation not in {"complete_no_more_doses"}
        return {
            "rule_id": rule["rule_id"],
            "pathway": "yellow_fever_age_5_59",
            "eligible": eligible,
            "requires_review": False,
            "recommendation": recommendation,
            "history_rule": history_rule,
        }

    return None


def _evaluate_hpv4(
    rule: dict[str, Any],
    *,
    age_months: int,
    hpv_doses_received: int | None,
    pregnant: bool | None,
) -> dict[str, Any] | None:
    population = rule.get("population") or {}
    min_age = int(population.get("min_age_months") or 108)
    max_age = int(population.get("max_age_months") or 179)
    if not (min_age <= age_months <= max_age):
        return None

    if pregnant is True:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "hpv4_routine",
            "eligible": False,
            "requires_review": False,
            "recommendation": "do_not_vaccinate_during_pregnancy",
            "reason": "pregnancy_contraindication",
        }

    if hpv_doses_received is None:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "hpv4_routine",
            "eligible": True,
            "requires_review": True,
            "recommendation": "verify_hpv_vaccination_history",
        }

    if hpv_doses_received >= 1:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "hpv4_routine",
            "eligible": False,
            "requires_review": False,
            "recommendation": "routine_schedule_complete",
        }

    return {
        "rule_id": rule["rule_id"],
        "pathway": "hpv4_routine",
        "eligible": True,
        "requires_review": False,
        "recommendation": "one_hpv4_dose",
        "schedule": rule.get("schedule"),
    }


def _evaluate_mmr(
    rule: dict[str, Any],
    *,
    age_months: int,
    mmr_doses_received: int | None,
    is_healthcare_worker: bool | None,
) -> dict[str, Any] | None:
    schedule = rule.get("schedule") or {}
    min_interval = int(schedule.get("min_interval_between_doses_days") or 30)

    if age_months < 12:
        # Dose zero/bloqueio são tratados por regras próprias.
        return None

    if mmr_doses_received is None:
        return {
            "rule_id": rule["rule_id"],
            "pathway": "mmr_routine",
            "eligible": True,
            "requires_review": True,
            "recommendation": "verify_mmr_vaccination_history",
        }

    if is_healthcare_worker is True:
        required = int(schedule.get("healthcare_worker_required_total_doses") or 2)
        remaining = max(0, required - mmr_doses_received)
        return {
            "rule_id": rule["rule_id"],
            "pathway": "mmr_healthcare_worker",
            "eligible": remaining > 0,
            "requires_review": False,
            "recommendation": (
                "complete_mmr_two_dose_schedule"
                if remaining > 0
                else "routine_schedule_complete"
            ),
            "required_total_doses": required,
            "remaining_doses": remaining,
            "min_interval_days": min_interval,
        }

    age_years = age_months / 12
    if age_years < 30:
        required = int(schedule.get("required_total_doses_through_age_29") or 2)
        remaining = max(0, required - mmr_doses_received)
        payload = {
            "rule_id": rule["rule_id"],
            "pathway": "mmr_routine_under_30",
            "eligible": remaining > 0,
            "requires_review": False,
            "recommendation": (
                "complete_mmr_two_dose_schedule"
                if remaining > 0
                else "routine_schedule_complete"
            ),
            "required_total_doses": required,
            "remaining_doses": remaining,
            "min_interval_days": min_interval,
        }
        if 12 <= age_months < 15 and mmr_doses_received == 1:
            payload["recommendation"] = "second_mmr_component_dose_at_15_months"
            payload["target_age_months"] = int(
                schedule.get("child_second_dose_age_months") or 15
            )
        return payload

    if age_years < 60:
        required = int(schedule.get("required_total_doses_age_30_59") or 1)
        remaining = max(0, required - mmr_doses_received)
        return {
            "rule_id": rule["rule_id"],
            "pathway": "mmr_routine_age_30_59",
            "eligible": remaining > 0,
            "requires_review": False,
            "recommendation": (
                "one_mmr_dose"
                if remaining > 0
                else "routine_schedule_complete"
            ),
            "required_total_doses": required,
            "remaining_doses": remaining,
        }

    return None


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
    menc_primary_complete: bool | None = None,
    days_since_last_menc: int | None = None,
    menacwy_child_booster_received: bool | None = None,
    menacwy_adolescent_dose_received: bool | None = None,
    yellow_fever_history: str = "unknown",
    days_since_last_yellow_fever_dose: int | None = None,
    hpv_doses_received: int | None = None,
    pregnant: bool | None = None,
    mmr_doses_received: int | None = None,
    is_healthcare_worker: bool | None = None,
    geographic_context: dict[str, Any] | None = None,
    on_date: date | None = None,
) -> dict[str, Any]:
    """Avalia caminhos configurados para suporte operacional.

    Regras em draft/onboarding nunca são retornadas por active_rules().
    """
    day = on_date or date.today()
    conditions = {int(x) for x in (condition_ids or [])}
    item = get_immunobiologic(immunobiologic_id)
    pathways: list[dict[str, Any]] = []

    for rule in active_rules(
        immunobiologic_id,
        on_date=day,
        geographic_context=geographic_context,
    ):
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
        elif immunobiologic_id == "menacwy" and strategy == "routine_menacwy":
            result = _evaluate_menacwy(
                rule,
                age_months=age_months,
                menc_primary_complete=menc_primary_complete,
                days_since_last_menc=days_since_last_menc,
                menacwy_child_booster_received=menacwy_child_booster_received,
                menacwy_adolescent_dose_received=menacwy_adolescent_dose_received,
            )
        elif immunobiologic_id == "febre_amarela" and strategy == "routine_yellow_fever":
            result = _evaluate_yellow_fever(
                rule,
                age_months=age_months,
                yellow_fever_history=yellow_fever_history,
                days_since_last_yellow_fever_dose=days_since_last_yellow_fever_dose,
            )
        elif immunobiologic_id == "hpv4" and strategy == "routine_hpv4":
            result = _evaluate_hpv4(
                rule,
                age_months=age_months,
                hpv_doses_received=hpv_doses_received,
                pregnant=pregnant,
            )
        elif immunobiologic_id == "triplice_viral" and strategy == "routine_mmr":
            result = _evaluate_mmr(
                rule,
                age_months=age_months,
                mmr_doses_received=mmr_doses_received,
                is_healthcare_worker=is_healthcare_worker,
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
