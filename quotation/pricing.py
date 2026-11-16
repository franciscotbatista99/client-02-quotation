from __future__ import annotations

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
    if not items:
        raise QuoteError("No items provided for quotation")

    # Load catalog prices
    catalog = load_catalog()

    # Process each item
    lines = []
    goods_net_cents = 0

    for item in items:
        # Validate item structure
        sku = item.get("sku")
        quantity = item.get("quantity")

        # Check for missing keys
        if sku is None or quantity is None:
            raise QuoteError(f"Item missing required keys: sku or quantity")

        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            raise QuoteError(f"Quantity must be at least 1 (got {quantity})")

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

from quotation.catalog import load_catalog
