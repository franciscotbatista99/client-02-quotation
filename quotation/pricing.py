"""HansePack quotation logic – STUB, to be implemented by the Factory (code implementer).

Contract (binding for the agent and the product tests, do not change the signature):

    calculate_quote(items: list[dict], rule_version: str = "HP-V1") -> dict

    items  = [{"sku": "HP-BOX", "quantity": 50}, ...]
    result = {
        "currency": "EUR",
        "rule_version": "HP-V1",
        "lines": [{"sku", "quantity", "unit_price_cents", "list_amount_cents",
                   "discount_percent", "discount_cents", "net_cents"}, ...],
        "goods_net_cents": int,
        "shipping_cents": int,
        "total_cents": int,
    }

Invalid input raises QuoteError with an understandable message – never a quote.
Prices come from quotation.catalog.load_catalog(); all money values are integer cents.
Deterministic Python only: no LLM, no network, no lookup of the customer's reference cases.
"""

from __future__ import annotations

from typing import Any


class QuoteError(ValueError):
    """Invalid quotation input (understandable message, no quote is produced)."""


def calculate_quote(items: list[dict[str, Any]], rule_version: str = "HP-V1") -> dict[str, Any]:
    raise NotImplementedError("calculate_quote is implemented by the Factory run (Session 6, Task 2)")
