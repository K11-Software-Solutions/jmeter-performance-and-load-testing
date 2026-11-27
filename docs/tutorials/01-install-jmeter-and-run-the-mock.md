# 01 · Install JMeter and run the mock API

> **Goal:** install Java and Apache JMeter, start the local mock API, and run your first test plan in both GUI and non-GUI mode.
>
> **Script:** `test-plans/01_hello_jmeter.jmx`

## 1. Install Java

JMeter 5.6.3 (the current release) needs Java 8 or later. Use a current LTS such as Java 17 or 21.

```powershell
java -version
```

If you get "not recognised", install a JDK (for example Eclipse Temurin or Oracle JDK 21) and open a new terminal.

## 2. Install JMeter

1. Download `apache-jmeter-5.6.3.zip` from the official page: <https://jmeter.apache.org/download_jmeter.cgi>
2. Optional but good practice: check the SHA-512 checksum published next to it.

   ```powershell
   Get-FileHash .\apache-jmeter-5.6.3.zip -Algorithm SHA512
   ```

3. Unzip it to a folder **without spaces**, for example `C:\tools\apache-jmeter-5.6.3`.
4. Add `C:\tools\apache-jmeter-5.6.3\bin` to your `PATH`, or set `JMETER_HOME` to `C:\tools\apache-jmeter-5.6.3` (the helper scripts in this repo use either).
5. Check it:

   ```powershell
   jmeter --version
   ```

On macOS you can also use `brew install jmeter`. On Linux, unzip the `.tgz` and add `bin` to your `PATH`.

### Optional: JMeter Plugins Manager

Many teams add the [JMeter Plugins Manager](https://jmeter-plugins.org/wiki/PluginsManager/) for extra thread groups and graphs. Everything in this repo uses **core JMeter only**, so you don't need it.

## 3. Start the mock API

The scripts never touch a real website. They run against a small Node.js server in this repo that uses synthetic data.

```powershell
node mock-server/server.js
```

You should see `K11 Claims Analytics mock API listening on http://localhost:3000`. Leave it running in its own terminal. Quick checks:

```powershell
curl.exe http://localhost:3000/health
```

Open <http://localhost:3000/portal/login> in a browser to see the HTML portal (user `analyst01`, password `learn-jmeter`). See [`mock-server/README.md`](../../mock-server/README.md) for every endpoint.

## 4. Run your first plan in the GUI

```powershell
jmeter -t test-plans/01_hello_jmeter.jmx
```

1. Press the green **Start** button.
2. Click **View Results Tree** and select `GET /health`. Look at the *Sampler result*, *Request* and *Response data* tabs.
3. Click **Summary Report** to see one sample, 0% errors.

The GUI is for **building and debugging** scripts. Don't use it for real load: drawing listeners uses a lot of CPU and memory and distorts your results.

## 5. Run it in non-GUI (CLI) mode

This is how real tests run:

```powershell
jmeter -n -t test-plans/01_hello_jmeter.jmx -l results/01.jtl
```

| Option | Meaning |
|---|---|
| `-n` | non-GUI mode |
| `-t` | the test plan to run |
| `-l` | where to write the results file (`.jtl`, CSV format by default) |

Then summarise the results with the helper script:

```powershell
python scripts/jtl_summary.py results/01.jtl
```

## 6. Run every tutorial plan at once

```powershell
python scripts/run_tutorials.py
```

This runs plans 01–10 in non-GUI mode (about 3 minutes) and fails if any sample fails. It is a good way to check your setup.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Connection refused` on every sample | The mock API is not running, or is on another port. Pass `-Jport=3001` if you changed it. |
| `jmeter is not recognized` | `bin` is not on your `PATH`; use the full path to `jmeter.bat`. |
| GUI is very slow | Too many listeners or results; clear them (broom icon) or use non-GUI mode. |
| `Error in NonGUIDriver ... already exists` | The results file or report folder exists; delete it or add `-f` to overwrite. |

## Check yourself

1. Why shouldn't you run a load test in GUI mode?
2. What is a `.jtl` file?

<details><summary>Answers</summary>

1. Listeners and the GUI use CPU and memory on the load generator, which slows JMeter itself down and skews results.
2. JMeter's results file: one row per sample with timestamp, elapsed time, label, response code, success flag, bytes, thread counts and more (CSV or XML).
</details>

**Next:** [02 · Test plan anatomy](02-test-plan-anatomy.md)
