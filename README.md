# client-02-quotation – HansePack quotation calculator

Quotation calculator for **HansePack Handelsgesellschaft**, a fictional B2B packaging supplier (HAW Hamburg course project, customer project 02, Sessions 6–8). Not a real offer: *Net amounts – course project, not a binding quotation.*

This is a separate product repository. It is developed through the team's existing Factory ([`cait33/agentic_ai`](https://github.com/cait33/agentic_ai), project config `projects/hansepack-02.json`) but **runs and is tested without the Factory, an LLM, a network or a database**.

Previous customer (Nordwerk website) is a different product: [`client-01-website`](https://github.com/franciscotbatista99/client-01-website), frozen at tag `v1.0` (`f1575ad`).

## Status

| Session | Scope | State |
|---|---|---|
| S6 (16.11.) | Repo, customer fixtures, Python calculation for HP-BOX × 1 / × 50, reject quantity 0 (HP-AC01 initial, HP-AC02, HP-AC04 E01) | in progress |
| S7 (23.11.) | All Q01–Q14 and E01–E10, simple web UI, JSON export, fresh-checkout release candidate | planned |
| S8 (30.11.) | Change request CR-02 (shipping rule HP-V2), release and handover | planned |

Customer issue with scope, open questions and assumptions: issue #N.

## Requirements

- Python 3.12
- `pytest` for the product checks (no runtime dependencies – standard library only)

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
| `tests/test_reference_cases.py` | Q01, Q03 (HP-AC02), E01 (HP-AC04), independence of `pricing.py` (HP-AC01) |

Test names follow `test_hp_acNN_*` so the Factory can map results to the HansePack acceptance criteria.
Until the Factory run of Session 6 task 2, `quotation/pricing.py` is a stub and the Q01/Q03/E01 checks are expected to fail.

## Start

The calculation module `quotation/pricing.py` is delivered by the Factory in Session 6 task 2. Planned reproducible call (same input format as the customer reference cases):

```bash
python -m quotation.pricing '{"items": [{"sku": "HP-BOX", "quantity": 50}]}'
```

## Structure

| Path | Content | Maintained by |
|---|---|---|
| `quotation/` | Business logic (Python, stdlib only) | Factory agent (only write area) + human review |
| `fixtures/` | Binding customer files, unchanged, with `SHA256SUMS` and [`SOURCE.md`](fixtures/SOURCE.md) | customer (read-only) |
| `tests/` | Product checks against the customer values | team (not the generating agent) |

## Rules for this repo

- Prices come only from `fixtures/HansePack_Katalog.json`; the expected results in `HansePack_Referenzfaelle.json` are used by tests only.
- Money as integer cents; discount per line, ROUND_HALF_UP to whole cents; no binary floating-point rounding; no price calculation by an LLM.
- Invalid input raises an understandable error in the Python business logic; no apparently valid quotation.
- Every change via pull request with green `python -m pytest` and a named human reviewer.