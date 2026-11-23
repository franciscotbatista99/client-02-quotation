"""HansePack JSON export – STUB, implemented by the Factory (Session 7, task 1).

Contract (binding for the agent, the web UI and tests/test_export.py – do not change the signature):

    quote_to_json(quote: dict) -> str

- `quote` is the dict returned by quotation.pricing.calculate_quote (already validated, money in integer cents).
- Returns a JSON text (UTF-8, ensure_ascii=False, indent=2) with exactly these customer fields:
  currency, rule_version, lines (per line: sku, quantity, unit_price_cents, list_amount_cents,
  discount_percent, discount_cents, net_cents), goods_net_cents, shipping_cents, total_cents.
- Values are copied unchanged from `quote`: no recalculation, no rounding, no float, no extra money fields.
- Deterministic: the same quote always gives the same text. Standard library `json` only.
The web UI displays exactly this text and offers it as download, so display and export cannot differ.
"""

from __future__ import annotations

from typing import Any


def quote_to_json(quote: dict[str, Any]) -> str:
    raise NotImplementedError("quote_to_json is implemented by the Factory run (Session 7, task 1)")
