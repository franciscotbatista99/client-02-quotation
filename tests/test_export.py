"""HP-AC06 – JSON export (Session 7). Expected values only from the customer reference file.

Contract for the export (agreed with Task 1, please keep it):
    quotation/export.py:  quote_to_json(quote: dict) -> str
The export is built from the SAME calculate_quote() result that the UI displays – no second calculation.
Optional extra fields (timestamp, quote number, R-02 calculation_note) are allowed and ignored here.
Skipped until quotation/export.py exists.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quotation.pricing import calculate_quote

export = pytest.importorskip("quotation.export", reason="quotation/export.py not implemented yet (Task 1)")

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "fixtures" / "HansePack_Referenzfaelle.json").read_text(encoding="utf-8"))
VALID = {case["id"]: case for case in REFERENCE["valid_cases"]}
LINE_FIELDS = ("sku", "quantity", "unit_price_cents", "list_amount_cents",
               "discount_percent", "discount_cents", "net_cents")
TOTAL_FIELDS = ("currency", "rule_version", "goods_net_cents", "shipping_cents", "total_cents")


def exported(case_id: str) -> tuple[dict, dict]:
    quote = calculate_quote(VALID[case_id]["input"]["items"], rule_version="HP-V1")
    return quote, json.loads(export.quote_to_json(quote))


@pytest.mark.parametrize("case_id", sorted(VALID))
def test_hp_ac06_export_matches_calculation(case_id):
    quote, data = exported(case_id)
    assert {f: data[f] for f in TOTAL_FIELDS} == {f: quote[f] for f in TOTAL_FIELDS}
    assert [{f: line[f] for f in LINE_FIELDS} for line in data["lines"]] == \
           [{f: line[f] for f in LINE_FIELDS} for line in quote["lines"]]


@pytest.mark.parametrize("case_id", sorted(VALID))
def test_hp_ac06_export_matches_customer_values(case_id):
    _, data = exported(case_id)
    assert {f: data[f] for f in TOTAL_FIELDS} == VALID[case_id]["expected"]["HP-V1"]
    assert [{f: line[f] for f in LINE_FIELDS} for line in data["lines"]] == VALID[case_id]["expected_lines"]


def test_hp_ac06_export_money_is_integer_cents_and_has_rule_version():
    _, data = exported("Q14")
    assert data["currency"] == "EUR" and data["rule_version"] == "HP-V1"
    money = [data["goods_net_cents"], data["shipping_cents"], data["total_cents"]]
    for line in data["lines"]:
        money += [line["unit_price_cents"], line["list_amount_cents"], line["discount_cents"], line["net_cents"]]
    assert all(type(v) is int for v in money)
