# client-02-quotation – HansePack quotation calculator

Quotation calculator for **HansePack Handelsgesellschaft**, a fictional B2B packaging supplier (HAW Hamburg course project, customer project 02, Sessions 6–8). Not a real offer: *Net amounts – course project, not a binding quotation.*

This is a separate product repository. It is developed through the team's existing Factory ([`cait33/agentic_ai`](https://github.com/cait33/agentic_ai), project config `projects/quotation-02.json`) but **runs and is tested without the Factory, an LLM, a network or a database**.

Previous customer (Nordwerk website) is a different product: [`client-01-website`](https://github.com/franciscotbatista99/client-01-website), frozen at tag `v1.0` (`f1575ad`).

## Status

| Session | Scope | State |
|---|---|---|
| S6 (16.11.) | Repo, customer fixtures, Python calculation for HP-BOX × 1 / × 50, reject quantity 0 (HP-AC01 initial, HP-AC02, HP-AC04 E01) | done |
| S7 (23.11.) | All Q01–Q14 and E01–E10, simple web UI, JSON export, fresh-checkout release candidate | in progress |
| S8 (30.11.) | Change request CR-02 (shipping rule HP-V2), release and handover | planned |

Customer issue with scope, open questions and assumptions: issue #2.

## Requirements

- Python 3.12
- No runtime dependencies – calculation, export and web UI use the standard library only
- `pytest` for the product checks

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Product tests

```bash
python -m pytest
```

| File | Checks |
|---|---|
| `tests/test_fixtures.py` | Customer fixtures byte-identical (sha256), catalogue = brief price table, Q01–Q14/E01–E10 present, product code does not read the expected answers |
| `tests/test_reference_cases.py` | Independence of `pricing.py` (HP-AC01), Q01/Q03 (HP-AC02), all Q01–Q14 line values + totals (HP-AC03), all E01–E10 rejected in Python, no type coercion / SKU aggregation (HP-AC04) |
| `tests/test_export.py` | JSON export = calculation = customer values for Q01–Q14, integer cents, rule version (HP-AC06) |
| `tests/test_web.py` | Web UI: page with form, net notice and download; API returns the customer values; invalid E01–E10 come back as an error; displayed text = exported JSON (HP-AC05/06) |

Test names follow `test_hp_acNN_*` so the Factory can map results to the HansePack acceptance criteria.
Expected values come only from `fixtures/HansePack_Referenzfaelle.json`, never from the generating agent.

## Start

Web UI (local, no Factory, no LLM, no database):

```bash
python -m quotation.web            # then open http://127.0.0.1:8000
python -m quotation.web --port 8080
```

Enter 1–3 lines (article + quantity), click **Berechnen**, then **JSON herunterladen**. The page shows
"Nettobeträge – Lehrprojekt, kein verbindliches Angebot". Every input is checked in the Python business logic;
invalid input shows an error and no quotation. The table and the download come from the same JSON text.

Command line (same input format as the customer reference cases):

```bash
python -m quotation.pricing '{"items": [{"sku": "HP-BOX", "quantity": 50}]}'
```

## Structure

| Path | Content | Maintained by |
|---|---|---|
| `quotation/pricing.py` | Calculation + validation (HP-V1) | Factory agent + human review |
| `quotation/export.py` | JSON export `quote_to_json` | Factory agent (S7 task 1) + human review |
| `quotation/web.py` | Local web UI + `/api/quote` (stdlib `http.server`) | team (human-written) |
| `quotation/catalog.py` | Loads the binding catalogue | team (human-written) |
| `fixtures/` | Binding customer files, unchanged, with `SHA256SUMS` and [`SOURCE.md`](fixtures/SOURCE.md) | customer (read-only) |
| `tests/` | Product checks against the customer values | team (not the generating agent) |

## Rules for this repo

- Prices come only from `fixtures/HansePack_Katalog.json`; the expected results in `HansePack_Referenzfaelle.json` are used by tests only.
- Money as integer cents; discount per line, ROUND_HALF_UP to whole cents; no binary floating-point rounding; no price calculation by an LLM.
- Invalid input raises an understandable error in the Python business logic; no apparently valid quotation.
- Every change via pull request with green `python -m pytest` and a named human reviewer.