from __future__ import annotations

import json
import sys
from typing import Any

from quotation.catalog import load_catalog

class QuoteError(ValueError):
    """Invalid quotation input (understandable message, no quote is produced)."""

def calculate_quote(items: list[dict[str, Any]], rule_version: str = "HP-V1") -> dict[str, Any]:
    """Calculate a HansePack quotation with HP-V1 rule version (deterministic).

    Args:
        items: List of items to quote, each item is a dict with keys: sku (str), quantity (int)
        rule_version: Rule version to use (must be "HP-V1")

    Returns:
        dict with keys: currency, rule_version, lines, goods_net_cents, shipping_cents, total_cents

    Raises:
        QuoteError: For invalid input (e.g., quantity <= 0, empty items, unknown SKU)
    """

    # Validate rule version
    if rule_version != "HP-V1":
        raise QuoteError(f"Rule version {rule_version} is not supported. Only HP-V1 is allowed.")

    # Validate input items
    if not isinstance(items, list) or not (1 <= len(items) <= 3):
        raise QuoteError("Quotation must contain between 1 and 3 items.")

    seen_skus: set[str] = set()

    # Load catalog prices
    catalog = load_catalog()

    # Process each item
    lines = []
    goods_net_cents = 0

    for item in items:
        if not isinstance(item, dict):
            raise QuoteError("Each quotation item must be an object with 'sku' and 'quantity'.")
        
        # Validate item structure
        sku = item.get("sku")
        quantity = item.get("quantity")

        # Check for missing keys
        if not isinstance(item, dict):
            raise QuoteError("Each quotation item must be an object with 'sku' and 'quantity'.")

        if not isinstance(sku, str) or not sku or quantity is None:
            raise QuoteError("Item missing required keys: sku or quantity.")

        if sku in seen_skus:
            raise QuoteError(f"Duplicate SKU not allowed: {sku}")
        seen_skus.add(sku)

        # Validate quantity
        if type(quantity) is not int or not (1 <= quantity <= 10000):
            raise QuoteError(f"Quantity must be an integer between 1 and 10000 (got {quantity!r}).")

        # Check if SKU exists in catalog
        if sku not in catalog:
            raise QuoteError(f"SKU {sku} not found in catalog")

        # Get unit price in cents
        unit_price_cents = catalog[sku]

        # Calculate list amount
        list_amount_cents = unit_price_cents * quantity

        # Apply discount based on quantity
        if quantity <= 49:
            discount_percent =  0
        elif quantity <= 99:
            discount_percent = 5
        else:
            discount_percent = 10

        # Calculate discount in cents (round half up)
        discount_cents = (list_amount_cents * discount_percent + 50) // 100

        # Calculate net amount
        net_cents = list_amount_cents - discount_cents

        # Add to goods net
        goods_net_cents += net_cents

        # Add line to result
        lines.append({
            "sku": sku,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "list_amount_cents": list_amount_cents,
            "discount_percent": discount_percent,
            "discount_cents": discount_cents,
            "net_cents": net_cents
        })

    # Calculate shipping
    shipping_cents = 1200 if goods_net_cents < 50000 else 0

    # Calculate total
    total_cents = goods_net_cents + shipping_cents

    # Return result
    return {
        "currency": "EUR",
        "rule_version": "HP-V1",
        "lines": lines,
        "goods_net_cents": goods_net_cents,
        "shipping_cents": shipping_cents,
        "total_cents": total_cents
    }

def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print JSON quotation to stdout or error to stderr."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Fehler: Exactly one JSON argument expected.", file=sys.stderr)
        return 2

    try:
        payload = json.loads(args[0])
        if isinstance(payload, dict) and "items" in payload:
            items = payload["items"]
            rule_version = payload.get("rule_version", "HP-V1")
        else:
            items = payload
            rule_version = "HP-V1"
        result = calculate_quote(items, rule_version=rule_version)
    except (json.JSONDecodeError, QuoteError, TypeError, ValueError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())