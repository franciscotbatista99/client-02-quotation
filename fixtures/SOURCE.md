# Customer fixtures – provenance

Both files are the binding customer inputs of HansePack (brief v1.0, 8 November 2026), copied **byte-for-byte unchanged**.
They are customer data, not output of our Factory or of any agent. Do not edit them; a change of the customer data needs a new customer version and a new commit with new checksums.

| File | Source (course repo / Factory) | sha256 | git blob |
|---|---|---|---|
| `HansePack_Katalog.json` | `cait33/agentic_ai` `task sheets/session-06-08/HansePack_Katalog.json`, added in commit `f66013c`, unchanged at `6a8a2af` | `70f0e1a7389b136828a794c79df130762d7638d9f63b373a7fd43e16607f953a` | `a11a9229bf4b75c8ea0f5753c9084b2f506d6d0b` |
| `HansePack_Referenzfaelle.json` | `cait33/agentic_ai` `task sheets/session-06-08/HansePack_Referenzfaelle.json`, added in commit `f66013c`, unchanged at `6a8a2af` | `7deb994e5debd82019062574ecfb1e445c4bd474e98b33fb532668ae00dc839a` | `86e9117ae9a441d9429c3645a459d9512391d89f` |

Check by hand:

```bash
cd fixtures && sha256sum -c SHA256SUMS      # Windows: Get-FileHash *.json
git hash-object HansePack_Katalog.json HansePack_Referenzfaelle.json   # must equal the git blob column
```

The automated checks `tests/test_fixtures.py` and `test_hp_ac01_fixtures_unchanged` fail if either file differs from these checksums.

Use:
- `HansePack_Katalog.json` – the price catalogue the product reads at runtime (single source of prices; no prices copied into code).
- `HansePack_Referenzfaelle.json` – expected results Q01–Q14 / E01–E10; used **only by tests**. Product code must not read it or return stored answers by case ID.