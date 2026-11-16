"""Product checks against the customer's reference values (Session 6).

Expected values come ONLY from the unchanged customer file fixtures/HansePack_Referenzfaelle.json
(sha256 in fixtures/SHA256SUMS) – never from the generating agent.

Today (S6): HP-AC01 (independence), HP-AC02 (Q01, Q03), first part of HP-AC04 (E01).
S7 extends TODAY_VALID / TODAY_INVALID to all Q01–Q14 / E01–E10.

Run:  python -m pytest tests -q
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from quotation.pricing import QuoteError, calculate_quote

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
REFERENCE = json.loads((FIXTURES / "HansePack_Referenzfaelle.json").read_text(encoding="utf-8"))
VALID = {case["id"]: case for case in REFERENCE["valid_cases"]}
INVALID = {case["id"]: case for case in REFERENCE["invalid_cases"]}
RULE_VERSION = "HP-V1"

TODAY_VALID = ["Q01", "Q03"]
TODAY_INVALID = ["E01"]
LINE_FIELDS = ("sku", "quantity", "unit_price_cents", "list_amount_cents",
               "discount_percent", "discount_cents", "net_cents")
TOTAL_FIELDS = ("currency", "rule_version", "goods_net_cents", "shipping_cents", "total_cents")


# --------------------------------------------------------------------------- #
# HP-AC01 – independent product, unchanged customer fixtures
# --------------------------------------------------------------------------- #
def test_hp_ac01_fixtures_unchanged():
    for line in (FIXTURES / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split()
        actual = hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
        assert actual == digest, f"customer fixture {name} was modified"


def test_hp_ac01_pricing_has_no_factory_or_llm_dependency():
    source = (ROOT / "quotation" / "pricing.py").read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"src", "langchain", "langchain_core", "langchain_ollama", "langgraph", "ollama",
                 "openai", "requests", "httpx", "urllib", "socket"}
    assert not imported & forbidden, f"product logic must run without Factory/LLM/network: {imported & forbidden}"


def test_hp_ac01_pricing_does_not_read_expected_results():
    source = (ROOT / "quotation" / "pricing.py").read_text(encoding="utf-8")
    for marker in ("Referenzfaelle", "valid_cases", "expected_lines", "Q01", "Q03"):
        assert marker not in source, f"product logic must calculate, not look up reference results ({marker!r})"


# --------------------------------------------------------------------------- #
# HP-AC02 – Q01 and Q03 fully correct (lines + totals) under HP-V1
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case_id", TODAY_VALID)
def test_hp_ac02_lines_match_customer_values(case_id):
    case = VALID[case_id]
    quote = calculate_quote(case["input"]["items"], rule_version=RULE_VERSION)
    lines = [{field: line[field] for field in LINE_FIELDS} for line in quote["lines"]]
    assert lines == case["expected_lines"]


@pytest.mark.parametrize("case_id", TODAY_VALID)
def test_hp_ac02_totals_match_customer_values(case_id):
    case = VALID[case_id]
    quote = calculate_quote(case["input"]["items"], rule_version=RULE_VERSION)
    assert {field: quote[field] for field in TOTAL_FIELDS} == case["expected"][RULE_VERSION]


@pytest.mark.parametrize("case_id", TODAY_VALID)
def test_hp_ac02_money_values_are_integer_cents(case_id):
    quote = calculate_quote(VALID[case_id]["input"]["items"], rule_version=RULE_VERSION)
    values = [quote["goods_net_cents"], quote["shipping_cents"], quote["total_cents"]]
    for line in quote["lines"]:
        values += [line["unit_price_cents"], line["list_amount_cents"], line["discount_cents"], line["net_cents"]]
    assert all(type(v) is int for v in values), "money values must be integer cents (no float)"


def test_hp_ac02_is_deterministic():
    items = VALID["Q03"]["input"]["items"]
    assert calculate_quote(items) == calculate_quote(items)


# --------------------------------------------------------------------------- #
# HP-AC04 (first part) – invalid input is rejected in the Python business logic
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("case_id", TODAY_INVALID)
def test_hp_ac04_invalid_input_is_rejected(case_id):
    with pytest.raises(QuoteError) as excinfo:
        calculate_quote(INVALID[case_id]["input"]["items"], rule_version=RULE_VERSION)
    assert str(excinfo.value).strip(), "error message must be understandable (not empty)"


@pytest.mark.parametrize("case_id", TODAY_INVALID)
def test_hp_ac04_invalid_input_does_not_mutate_items(case_id):
    items = json.loads(json.dumps(INVALID[case_id]["input"]["items"]))
    with pytest.raises(QuoteError):
        calculate_quote(items)
    assert items == INVALID[case_id]["input"]["items"], "no silent conversion of invalid input"
