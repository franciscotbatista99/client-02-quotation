from __future__ import annotations

import json
from typing import Any

"""Export a quotation as JSON text.

This function takes a validated quote dictionary and returns a JSON string
with the exact structure defined in the interface specification.

The output matches the visible calculation exactly, using integer cents for all
monetary values.

Note: This function does not recalculate any values; it copies the input quote
unchanged.
"""

def quote_to_json(quote: dict[str, Any]) -> str:
    return json.dumps({
        'currency': quote['currency'],
        'rule_version': quote['rule_version'],
        'lines': [
            {
                'sku': line['sku'],
                'quantity': line['quantity'],
                'unit_price_cents': line['unit_price_cents'],
                'list_amount_cents': line['list_amount_cents'],
                'discount_percent': line['discount_percent'],
                'discount_cents': line['discount_cents'],
                'net_cents': line['net_cents']
            }
            for line in quote['lines']
        ],
        'goods_net_cents': quote['goods_net_cents'],
        'shipping_cents': quote['shipping_cents'],
        'total_cents': quote['total_cents']
    }, ensure_ascii=False, indent=2)
