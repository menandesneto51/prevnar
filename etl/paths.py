"""Shared paths for Radar Vacinal ETL."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REF = DATA / "reference"
RAW = DATA / "raw"
MART = DATA / "mart"
MANUAL = DATA / "manual"
SIT1 = MANUAL / "situacao1"
TEMPLATES = MANUAL / "templates"

for d in (RAW, MART, SIT1, TEMPLATES, DATA / "warehouse"):
    d.mkdir(parents=True, exist_ok=True)

UF_CODES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
