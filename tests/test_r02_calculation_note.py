import json

from quotation.export import quote_to_json
from quotation.pricing import calculate_quote


def test_r02_calculation_note_in_export():
    data = json.loads(quote_to_json(calculate_quote([{"sku": "HP-BOX", "quantity": 1}])))
    assert data["calculation_note"] == "Net amounts; shipping shown separately."
