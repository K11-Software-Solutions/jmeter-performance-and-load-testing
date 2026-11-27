# 03 · Recording vs scripting

> **Goal:** record a browser journey with JMeter's HTTP(S) Test Script Recorder, and learn how to clean the recording up into a maintainable script. Know when to record and when to script by hand.
>
> **Script:** `test-plans/03_recorded_portal_flow.jmx` (the cleaned-up result of recording the mock portal)

## Two ways to build a script

| | Recording | Scripting by hand |
|---|---|---|
| How | JMeter acts as a proxy and captures every request your browser sends | You add samplers yourself from API docs, Swagger/OpenAPI or browser DevTools |
| Good for | Web UIs with many requests per page, legacy apps, discovering what a page really calls | REST APIs, microservices, anything with good API docs |
| Downsides | Captures noise (images, analytics, fonts), hard-coded tokens and IDs, awkward names | Slower to start; you can miss calls the browser makes |

In practice most people **record to discover, then script to maintain**. For API-first systems like the Claims Summary API, scripting by hand is usually faster and cleaner.

## Record the mock portal (GUI exercise)

The recorder needs the GUI and a browser, so this part is manual.

1. Start the mock API: `node mock-server/server.js`
2. In JMeter: **File → Templates… → Recording → Create**. Set the host to `localhost`. This adds a Thread Group, a Recording Controller, HTTP Request Defaults, a Cookie Manager and the **HTTP(S) Test Script Recorder** (port 8888).
3. Point your browser at the proxy `localhost:8888`. A separate browser profile is easiest (Firefox lets you set a proxy per profile). Note that many browsers bypass the proxy for `localhost`. If nothing is captured, browse to `http://127.0.0.1.nip.io:3000` or use your machine's LAN IP instead, or set Firefox's `network.proxy.allow_hijacking_localhost` to `true`.
4. For HTTPS sites JMeter creates a temporary root certificate, `ApacheJMeterTemporaryRootCA.crt`, in its `bin` folder. You would import it into the browser. The mock is plain HTTP, so you can skip this.
5. Press **Start** on the recorder, then in the browser:
   - open `/portal/login`
   - sign in as `analyst01` / `learn-jmeter`
   - run the Claims Summary for P1001, January 2026
   - sign out
6. Press **Stop**. Your requests are under the Recording Controller.

## Clean up the recording

A raw recording works once, then fails or misleads. Cleaning it up is the real skill:

1. **Remove noise.** Delete requests for favicons, images, CSS, fonts and third-party analytics. In the recorder's *Requests Filtering* tab you can exclude them up front with patterns such as `.*\.(png|jpg|gif|css|js|ico|woff2?)`.
2. **Rename samplers** to something readable, for example `POST /portal/login`, and group steps in **Transaction Controllers** (`TX02_Portal_Sign_In`).
3. **Move host and port** into HTTP Request Defaults so you can switch environments.
4. **Correlate dynamic values.** The recording contains the `_csrf` value from *your* session. Replay it and the server answers 403. Replace it with a Regular Expression Extractor (`name="_csrf" value="([^"]+)"`) and use `${csrf}` (Tutorial 05).
5. **Parameterise test data** such as user names and provider IDs with a CSV file (Tutorial 04).
6. **Add assertions** so a login page returned by mistake is not counted as a success (Tutorial 06).
7. **Add think time** between steps (Tutorial 07).

`03_recorded_portal_flow.jmx` is the result of steps 1–4, 6 and 7. Run it:

```powershell
jmeter -n -t test-plans/03_recorded_portal_flow.jmx -l results/03.jtl
python scripts/jtl_summary.py results/03.jtl
```

You will see labels like `POST /portal/login-0` and `POST /portal/login-1`. These are **sub-samples**: the POST returns a redirect (302) and JMeter follows it to `/portal/home`. The parent sample's time includes both.

## Other ways to capture traffic

- **Browser DevTools → Network tab:** copy a request as cURL and rebuild it as an HTTP Request.
- **Swagger / OpenAPI docs:** script each endpoint directly.
- **Third-party browser extensions** that export `.jmx` files exist. Treat their output like any recording: clean it up and check it.

## Check yourself

1. Why does a recorded script often fail when you replay it?
2. When would you choose scripting over recording?

<details><summary>Answers</summary>

1. It replays hard-coded dynamic values (session IDs, CSRF tokens, record IDs) that the server no longer accepts.
2. For APIs with good documentation, or when you want a small, clean, maintainable script.
</details>

**Next:** [04 · Parameterisation with CSV](04-parameterisation-with-csv.md)
