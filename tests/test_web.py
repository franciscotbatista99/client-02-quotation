"""HP-AC05 / HP-AC06 – small web UI (Session 7). Runs the real local server on a free port.

- Every input reaches the Python business logic: invalid cases E01–E10 come back as an error, never as a quote.
- POST /api/quote returns exactly quotation.export.quote_to_json(calculate_quote(...)) – the page renders and
  downloads this same text, so display and export cannot differ.
Expected values only from the customer reference file.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from quotation.export import quote_to_json
from quotation.pricing import calculate_quote
from quotation.web import NET_NOTICE, make_server

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = json.loads((ROOT / "fixtures" / "HansePack_Referenzfaelle.json").read_text(encoding="utf-8"))
VALID = {c["id"]: c for c in REFERENCE["valid_cases"]}
INVALID = {c["id"]: c for c in REFERENCE["invalid_cases"]}
MULTI_LINE = [cid for cid, c in VALID.items() if len(c["input"]["items"]) > 1]


@pytest.fixture(scope="module")
def base_url():
    server = make_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def request(url: str, body: object | None = None) -> tuple[int, str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                 method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return res.status, res.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8")


def test_hp_ac05_page_has_form_net_notice_and_download(base_url):
    status, html = request(base_url + "/")
    assert status == 200
    assert NET_NOTICE == "Nettobeträge – Lehrprojekt, kein verbindliches Angebot"
    assert NET_NOTICE in html
    for marker in ('id="quote-form"', 'id="calculate"', 'id="download"', 'id="error"', "HP-BOX", "HP-TAPE", "HP-FILM"):
        assert marker in html


@pytest.mark.parametrize("case_id", sorted(VALID))
def test_hp_ac05_api_returns_customer_values(base_url, case_id):
    status, text = request(base_url + "/api/quote", VALID[case_id]["input"])
    assert status == 200
    data = json.loads(text)
    expected = VALID[case_id]["expected"]["HP-V1"]
    assert {k: data[k] for k in expected} == expected
    fields = VALID[case_id]["expected_lines"][0].keys()
    assert [{k: line[k] for k in fields} for line in data["lines"]] == VALID[case_id]["expected_lines"]


@pytest.mark.parametrize("case_id", MULTI_LINE or ["Q12"])
def test_hp_ac06_displayed_text_is_exactly_the_export(base_url, case_id):
    items = VALID[case_id]["input"]["items"]
    status, text = request(base_url + "/api/quote", {"items": items})
    assert status == 200
    assert text == quote_to_json(calculate_quote(items))


@pytest.mark.parametrize("case_id", sorted(INVALID))
def test_hp_ac05_invalid_input_reaches_python_and_shows_error(base_url, case_id):
    status, text = request(base_url + "/api/quote", INVALID[case_id]["input"])
    assert status == 422
    data = json.loads(text)
    assert data["error"].strip() and "total_cents" not in data


def test_hp_ac05_malformed_request_is_an_error(base_url):
    status, text = request(base_url + "/api/quote", ["not", "an", "object"])
    assert status == 400 and json.loads(text)["error"]
