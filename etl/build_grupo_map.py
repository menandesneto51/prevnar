"""Parse BRGrupoAtendimento FHIR dump into reference JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path

from paths import REF

SRC = Path(
    r"C:\Users\Menandesneto\.cursor\projects\c-Users-Menandesneto-OneDrive-rea-de-Trabalho-prevnar"
    r"\agent-tools\492dc61b-8c51-4578-8a30-fe015c3897dd.txt"
)

# Mapeamento manual grupo → condição NT52 (parcial; proxy até CID)
MANUAL = {
    "000101": {"condicao_id": 1, "nota": "HIV/Aids (grupo)"},
    "000102": {"condicao_id": 2, "nota": "Pessoas com câncer / oncológicos"},
    "000103": {"condicao_id": 19, "nota": "Diabetes Mellitus"},
    "000104": {"condicao_id": 15, "nota": "Cardiopatia crônica (proxy)"},
    "000105": {"condicao_id": 13, "nota": "Doença respiratória crônica (proxy)"},
    "000106": {"condicao_id": 14, "nota": "Asma (proxy)"},
    "000107": {"condicao_id": 16, "nota": "Doença hepática crônica (proxy)"},
    "000108": {"condicao_id": 12, "nota": "Doença renal crônica (proxy)"},
    "000109": {"condicao_id": 3, "nota": "Transplantados órgão sólido"},
    "000110": {"condicao_id": 4, "nota": "Transplantados medula / TCTH"},
    "000111": {"condicao_id": 6, "nota": "Asplenia"},
    "000112": {"condicao_id": 7, "nota": "Imunodeficiência primária"},
    "000113": {"condicao_id": 10, "nota": "Imunossuprimidos / terapia"},
    "000114": {"condicao_id": 17, "nota": "Doença neurológica (proxy)"},
    "000115": {"condicao_id": 8, "nota": "Fibrose cística / outras (verificar)"},
    "000116": {"condicao_id": 11, "nota": "Implante coclear (proxy)"},
    "000117": {"condicao_id": 10, "nota": "Imunocomprometidos (amplo)"},
    "000120": {"condicao_id": 12, "nota": "Diálise / DRC (proxy)"},
}


def main() -> None:
    text = SRC.read_text(encoding="utf-8", errors="replace")
    pairs = re.findall(r'"code"\s*:\s*"(\d+)"\s*,\s*"display"\s*:\s*"([^"]+)"', text)
    if not pairs:
        pairs = re.findall(r"code\"\s*:\s*\"(\d+)\"[\s\S]{0,120}?display\"\s*:\s*\"([^\"]+)\"", text)
    catalog = [{"codigo": c, "nome": d} for c, d in pairs]
    (REF / "grupo_atendimento_catalog.json").write_text(
        json.dumps({"fonte": "BRGrupoAtendimento FHIR", "itens": catalog}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"catalog {len(catalog)}")
    for c, d in catalog:
        if c in MANUAL or any(
            k in d.lower()
            for k in (
                "hiv",
                "câncer",
                "cancer",
                "transplant",
                "diabetes",
                "imuno",
                "fibrose",
                "renal",
                "dial",
                "asma",
                "cardio",
                "hepato",
                "asplen",
                "coclear",
                "neuro",
                "pneumo",
                "nefro",
            )
        ):
            print(c, d, "->", MANUAL.get(c))

    mapped = []
    for codigo, meta in MANUAL.items():
        nome = next((x["nome"] for x in catalog if x["codigo"] == codigo), None)
        mapped.append(
            {
                "codigo_grupo_atendimento": codigo,
                "nome_grupo": nome,
                "condicao_id": meta["condicao_id"],
                "nota": meta["nota"],
                "proxy": True,
            }
        )
    out = {
        "versao": "1.0",
        "nota": (
            "Proxy grupo_atendimento→NT52 até CSV CKAN com motivo_indicacao_CID. "
            "Não substitui CID para cobertura Sit.1 definitiva."
        ),
        "mapeamentos": mapped,
    }
    path = REF / "grupo_atendimento_condicao_map.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path} ({len(mapped)} maps)")


if __name__ == "__main__":
    main()
