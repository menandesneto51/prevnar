from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "etl"
if str(ETL) not in sys.path:
    sys.path.insert(0, str(ETL))

from release_guardian import SECRET_PATTERNS, validate_cpf


def test_cpf_checksum_accepts_valid_constructed_value() -> None:
    # Montado em partes para não versionar o número completo como dado literal escaneável.
    value = "".join(["529", "982", "247", "25"])
    assert validate_cpf(value) is True


def test_cpf_checksum_rejects_repeated_digits() -> None:
    assert validate_cpf("1" * 11) is False


def test_secret_patterns_detect_constructed_github_token() -> None:
    value = "ghp" + "_" + ("A" * 24)
    assert any(pattern.search(value) for _, pattern in SECRET_PATTERNS)


def test_secret_patterns_do_not_flag_normal_configuration_text() -> None:
    value = "NEXT_PUBLIC_BASE_PATH=/prevnar"
    assert not any(pattern.search(value) for _, pattern in SECRET_PATTERNS)
