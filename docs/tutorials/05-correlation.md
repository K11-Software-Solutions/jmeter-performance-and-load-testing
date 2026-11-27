# 05 · Correlation with extractors

> **Goal:** capture dynamic values from one response and reuse them in later requests, using the JSON, Regular Expression and Boundary extractors.
>
> **Script:** `test-plans/05_correlation.jmx`

## The problem

Servers generate values per session or per request: auth tokens, CSRF tokens, session IDs, record IDs, report IDs. If your script sends a hard-coded copy, the server rejects it, or worse, quietly returns an error page that *looks* like a fast success.

**Correlation** = find the dynamic value → extract it into a variable → send the variable in the next request.

## How to find what to correlate

1. Run the flow twice in a browser (or record it twice) and compare the requests. Values that change between runs need correlating.
2. Look for values in request bodies, URLs and headers that first appeared in an earlier **response**.
3. Typical names: `token`, `access_token`, `_csrf`, `__VIEWSTATE`, `sessionId`, `id`, `reportId`.

## The journey in plan 05

| Step | Response contains | Extractor | Variable | Used in |
|---|---|---|---|---|
| `GET /portal/login` | `<input type="hidden" name="_csrf" value="...">` | Regular Expression | `csrf` | `POST /portal/login` form field `_csrf` |
| | (the same value) | Boundary | `csrf_boundary` | for comparison |
| `POST /api/auth/login` | `{"token":"..."}` | JSON | `token` | header `Authorization: Bearer ${token}` |
| `GET /api/providers` | `{"providers":[{"providerId":"P1001"}...]}` | JSON, match no. 0 | `randomProvider` | the report query |
| `GET /api/reports/claims-summary` | `{"reportId":"rpt-..."}` | JSON | `reportId` | export request body |
| `POST .../export` | `{"exportId":"exp-..."}` | JSON | `exportId` | the status URL path |

## The extractors

### JSON Extractor (for JSON APIs)

| Field | Example | Notes |
|---|---|---|
| Names of created variables | `token` | |
| JSON Path expressions | `$.token` | `$.providers[*].providerId` for every provider |
| Match No. | `1` | `1` = first match, `0` = random match, `-1` = all matches as `name_1`, `name_2`, … plus `name_matchNr` |
| Default value | `TOKEN_NOT_FOUND` | Always set a recognisable default so failures are obvious |

### Regular Expression Extractor (for HTML, headers, anything)

| Field | Example |
|---|---|
| Reference name | `csrf` |
| Regular expression | `name="_csrf" value="([^"]+)"` |
| Template | `$1$` (the first capture group) |
| Match No. | `1` |
| Default value | `CSRF_NOT_FOUND` |

Tips: keep the expression as specific as possible, use `([^"]+)` rather than `(.+)` (which is greedy), and set *Field to check* to **Response Headers** when the value is in a header such as `Location`.

### Boundary Extractor

Give it the text to the left and right of the value: `name="_csrf" value="` and `"`. It is simpler and faster than a regex for fixed surroundings.

Other options: the **CSS Selector Extractor** (`input[name=_csrf]`, attribute `value`) for HTML, and the **XPath** extractors for XML.

## Using the values

- Header Manager: `Authorization: Bearer ${token}`
- Body: `{"reportId":"${reportId}","format":"CSV"}`
- Path: `/api/reports/exports/${exportId}`

## See what breaks without correlation

Plan 05 contains a **disabled** sampler named `ANTI-PATTERN: hard-coded token`. Enable it in the GUI and run: it returns **401 Unauthorized** because the recorded token is stale. Without an assertion on the status code, some tools and some scripts would still count that as a quick, successful response.

## Debugging correlation

- Add a **Debug Sampler** (there is a disabled one in plan 05) and look at its response in View Results Tree to see every variable.
- In View Results Tree, the response panel has **RegExp Tester**, **JSON Path Tester** and **CSS Selector Tester** modes. Test your expression against a real response before running.
- If a variable shows its default (`..._NOT_FOUND`), the extractor didn't match. Check the scope: is the extractor *under* the right sampler?

## Run it

```powershell
jmeter -n -t test-plans/05_correlation.jmx -l results/05.jtl
python scripts/jtl_summary.py results/05.jtl --fail-on-errors
```

## Interview angle

> "Parameterisation replaces inputs I control with data from a file, so every virtual user is different. Correlation captures values the server generates, like a token or a record ID, and passes them into later requests. Without it the script works once and then fails, or quietly returns errors that look fast. I find candidates by recording twice and diffing, extract with a JSON or regex extractor with a clear default value, and always assert on the following request so a broken correlation shows up as an error."

**Next:** [06 · Assertions](06-assertions.md)
