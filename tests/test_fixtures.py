"""Provenance checks for the customer fixtures (HP-AC01 groundwork, Session 6 task 1).

These checks are written by the team, not by the generating agent. They make sure
- the customer files are byte-identical to the versions handed over by HansePack,
- the catalogue still matches the price table of the client brief,
- the product code never reads the expected answers (no lookup by case ID).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"

# sha256 of the customer files as delivered (see fixtures/SOURCE.md)
EXPECTED_SHA256 = {
    "HansePack_Katalog.json": "70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a",
    "HansePack_Referenzfaelle.json": "7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a",
}

# Price table of the client brief v1.0 (independent of the JSON file)
BRIEF_PRICES_CENTS = {"HP-BOX": 250, "HP-TAPE": 400, "HP-FILM": 1250}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fixtures_are_unchanged_customer_files() -> None:
    for name, digest in EXPECTED_SHA256.items():
        assert sha256(FIXTURES / name) == digest, f"{name} differs from the customer version"


def test_sha256sums_file_matches() -> None:
    listed = dict(reversed(line.split()) for line in (FIXTURES / "SHA256SUMS").read_text().splitlines() if line)
    assert listed == EXPECTED_SHA256


def test_catalogue_matches_brief_price_table() -> None:
    catalogue = json.loads((FIXTURES / "HansePack_Katalog.json").read_text(encoding="utf-8"))
    assert catalogue["currency"] == "EUR" and catalogue["money_unit"] == "integer_cents"
    prices = {p["sku"]: p["unit_price_cents"] for p in catalogue["products"]}
    assert prices == BRIEF_PRICES_CENTS


def test_reference_cases_are_complete() -> None:
    ref = json.loads((FIXTURES / "HansePack_Referenzfaelle.json").read_text(encoding="utf-8"))
    assert [c["id"] for c in ref["valid_cases"]] == [f"Q{n:02d}" for n in range(1, 15)]
    assert [c["id"] for c in ref["invalid_cases"]] == [f"E{n:02d}" for n in range(1, 11)]


def test_product_code_does_not_use_reference_answers() -> None:
    """Brief: product logic must not return stored answers by case ID."""
    for source in (ROOT / "quotation").rglob("*.py"):
        text = source.read_text(encoding="utf-8")
        assert "Referenzfaelle" not in text, f"{source.name} reads the reference answers"