"""Small local web UI for the HansePack quotation calculator (human-written, standard library only).

Start:   python -m quotation.web            -> http://127.0.0.1:8000
         python -m quotation.web --port 8080

- The page lets the user enter 1–3 lines (article + quantity), calculate and download the result as JSON.
- Every input goes unchanged to quotation.pricing.calculate_quote: validation happens ONLY in the Python
  business logic (the page does not block or convert invalid values, it just shows the server error).
- POST /api/quote returns exactly the text of quotation.export.quote_to_json(quote); the page renders the
  table from that text and the download button saves the same text -> display and export cannot differ.
No Factory, no LLM, no network access, no database.
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from quotation.catalog import CATALOG_FILE
from quotation.export import quote_to_json
from quotation.pricing import QuoteError, calculate_quote

NET_NOTICE = "Nettobeträge – Lehrprojekt, kein verbindliches Angebot"

PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HansePack – Angebotsrechner</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #1d2733; }
  h1 { font-size: 1.5rem; margin-bottom: .25rem; }
  .notice { background: #fff4d6; border: 1px solid #e6c25a; padding: .5rem .75rem; border-radius: 6px; }
  table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
  th, td { border-bottom: 1px solid #d8dde3; padding: .4rem .5rem; text-align: right; }
  th:first-child, td:first-child { text-align: left; }
  .row { display: flex; gap: .5rem; margin: .4rem 0; }
  select, input, button { font: inherit; padding: .35rem .5rem; }
  button { cursor: pointer; }
  .error { color: #a3121b; background: #fde8ea; border: 1px solid #f0a8ae; padding: .5rem .75rem; border-radius: 6px; }
  .totals td { font-weight: 600; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
<h1>HansePack – Angebotsrechner</h1>
<p class="notice" id="net-notice">__NET_NOTICE__</p>

<form id="quote-form">
  <div id="lines"></div>
  <div class="row">
    <button type="submit" id="calculate">Berechnen</button>
    <button type="button" id="download" disabled>JSON herunterladen</button>
  </div>
</form>

<p class="error" id="error" role="alert" hidden></p>
<section id="result" hidden>
  <table>
    <thead><tr><th>SKU</th><th>Menge</th><th>Einzelpreis</th><th>Listenbetrag</th><th>Rabatt %</th><th>Rabatt</th><th>Netto</th></tr></thead>
    <tbody id="result-lines"></tbody>
    <tfoot>
      <tr class="totals"><td colspan="6">Warenwert</td><td id="goods"></td></tr>
      <tr class="totals"><td colspan="6">Versand</td><td id="shipping"></td></tr>
      <tr class="totals"><td colspan="6">Gesamt (netto)</td><td id="total"></td></tr>
    </tfoot>
  </table>
  <p id="meta"></p>
</section>

<script>
const ARTICLES = __ARTICLES__;
const euro = c => (c / 100).toLocaleString("de-DE", {style: "currency", currency: "EUR"}) + " (" + c + " ct)";
const lines = document.getElementById("lines");
for (let i = 0; i < 3; i++) {
  const opts = ['<option value="">– kein Artikel –</option>']
    .concat(ARTICLES.map(a => `<option value="${a.sku}">${a.sku} – ${a.name}</option>`)).join("");
  lines.insertAdjacentHTML("beforeend",
    `<div class="row"><select name="sku" aria-label="Artikel ${i + 1}">${opts}</select>` +
    `<input name="quantity" aria-label="Menge ${i + 1}" placeholder="Menge"></div>`);
}
let lastExport = null;

function collectItems() {
  // No client-side validation: every entered value is sent as-is and checked in Python.
  const items = [];
  document.querySelectorAll("#lines .row").forEach(row => {
    const sku = row.querySelector("select").value;
    const raw = row.querySelector("input").value.trim();
    if (!sku && raw === "") return;
    const quantity = raw !== "" && !isNaN(Number(raw)) ? Number(raw) : raw;
    items.push({sku: sku, quantity: quantity});
  });
  return items;
}

document.getElementById("quote-form").addEventListener("submit", async ev => {
  ev.preventDefault();
  const error = document.getElementById("error"), result = document.getElementById("result");
  const download = document.getElementById("download");
  error.hidden = true; result.hidden = true; download.disabled = true; lastExport = null;
  const res = await fetch("/api/quote", {method: "POST", headers: {"Content-Type": "application/json"},
                                         body: JSON.stringify({items: collectItems()})});
  const text = await res.text();
  if (!res.ok) { error.textContent = "Fehler: " + JSON.parse(text).error; error.hidden = false; return; }
  const q = JSON.parse(text);
  document.getElementById("result-lines").innerHTML = q.lines.map(l =>
    `<tr><td>${l.sku}</td><td>${l.quantity}</td><td>${euro(l.unit_price_cents)}</td><td>${euro(l.list_amount_cents)}</td>` +
    `<td>${l.discount_percent} %</td><td>${euro(l.discount_cents)}</td><td>${euro(l.net_cents)}</td></tr>`).join("");
  document.getElementById("goods").textContent = euro(q.goods_net_cents);
  document.getElementById("shipping").textContent = euro(q.shipping_cents);
  document.getElementById("total").textContent = euro(q.total_cents);
  document.getElementById("meta").textContent = "Währung " + q.currency + " · Regelversion " + q.rule_version;
  result.hidden = false; lastExport = text; download.disabled = false;
});

document.getElementById("download").addEventListener("click", () => {
  if (!lastExport) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([lastExport], {type: "application/json"}));
  a.download = "hansepack-angebot.json";
  a.click();
});
</script>
</body>
</html>
"""


def render_page() -> str:
    catalog = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    articles = [{"sku": p["sku"], "name": p.get("name_de", p["sku"])} for p in catalog["products"]]
    return PAGE.replace("__NET_NOTICE__", NET_NOTICE).replace("__ARTICLES__", json.dumps(articles, ensure_ascii=False))


def handle_quote(body: bytes) -> tuple[int, str]:
    """Returns (HTTP status, JSON text). Success: exactly quote_to_json(calculate_quote(...))."""
    try:
        payload: Any = json.loads(body.decode("utf-8") or "null")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HTTPStatus.BAD_REQUEST, json.dumps({"error": "Request body is not valid JSON."})
    if not isinstance(payload, dict) or "items" not in payload:
        return HTTPStatus.BAD_REQUEST, json.dumps({"error": "Expected a JSON object with 'items'."})
    try:
        quote = calculate_quote(payload["items"], rule_version=payload.get("rule_version", "HP-V1"))
    except QuoteError as exc:
        return HTTPStatus.UNPROCESSABLE_ENTITY, json.dumps({"error": str(exc)}, ensure_ascii=False)
    return HTTPStatus.OK, quote_to_json(quote)


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, content_type: str, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(HTTPStatus.OK, "text/html", render_page())
        else:
            self._send(HTTPStatus.NOT_FOUND, "application/json", json.dumps({"error": "not found"}))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/quote":
            self._send(HTTPStatus.NOT_FOUND, "application/json", json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length") or 0)
        status, text = handle_quote(self.rfile.read(length))
        self._send(status, "application/json", text)

    def log_message(self, format: str, *args: Any) -> None:  # keep test output quiet
        pass


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HansePack quotation calculator (local web UI)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    server = make_server(args.host, args.port)
    print(f"HansePack Angebotsrechner: http://{args.host}:{server.server_address[1]}  ({NET_NOTICE}) – Ctrl+C beendet")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
