# 11 · Distributed testing

> **Goal:** generate more load than one machine can by running the same test plan on several load generators, controlled from one machine.
>
> **Script:** `test-plans/10_claims_summary_load.jmx` (unchanged; distributed mode is a run-time choice)

## When you need it

One JMeter machine can usually run hundreds to a few thousand threads, depending on think time, response sizes, assertions and the hardware. You need more machines when:

- the load generator's CPU goes above about 80%, or memory or network is saturated,
- the target load is beyond what one machine can produce,
- you want load from several network locations.

If the load generator is overloaded, response times include JMeter's own waiting time, and your results are wrong.

## How it works

```
                 ┌──────────────► Load generator 1 (jmeter-server) ──┐
Controller ──────┼──────────────► Load generator 2 (jmeter-server) ──┼──► System under test
(jmeter -n -R)   └──────────────► Load generator 3 (jmeter-server) ──┘
      ▲                         results stream back
      └──────────────────────────────────────────────────────────────┘
```

- The **controller** (client) sends the test plan to each **load generator** (server) over Java RMI.
- Each load generator runs the **whole plan with the full thread count**. 3 generators × 100 users = **300 users**.
- Results are sent back to the controller, which writes the single `.jtl` file and can build the HTML report.

## Rules that save hours

1. **Same versions everywhere:** the same JMeter version, Java version and plugins on the controller and every generator.
2. **Data files on every generator.** The CSV Data Set Config reads the file *on the generator*, so `users.csv` must exist there at the path the plan expects. To avoid two generators logging in as the same users, give each one a different slice of the data.
3. **Use `-G`, not `-J`, for the load generators.** `-Jusers=100` only sets the property on the controller. `-Gusers=100` sends it to every generator.
4. **Networking:** RMI needs the registry port (1099 by default) and a second port open. Fix the second one with `server.rmi.localport` so you can open it in the firewall. Keep the controller and generators on the same network; RMI over the internet is painful.
5. **RMI over SSL** is on by default since JMeter 4.0. Create a keystore once with `bin/create-rmi-keystore` (or the `keytool` command below) and copy `rmi_keystore.jks` to the controller and every generator. Turning SSL off (`server.rmi.ssl.disable=true`) is possible, but it leaves the RMI port open to anyone on the network, so avoid it outside a fully isolated lab.
6. **Results traffic:** the default sample sender (`StrippedBatch`) sends results in batches without response data, which keeps the controller from becoming a bottleneck. Leave it.

## Step by step

**Once:** create the RMI keystore and copy it to every machine (controller and generators).

```powershell
keytool -genkeypair -alias rmi -keyalg RSA -keysize 2048 -validity 7 -keystore rmi_keystore.jks `
  -storepass changeit -keypass changeit -dname "CN=rmi"
```

JMeter looks for `rmi_keystore.jks` with alias `rmi` and password `changeit` by default (the `server.rmi.ssl.keystore.*` properties). Pass the path with `-Jserver.rmi.ssl.keystore.file=...` and `-Jserver.rmi.ssl.truststore.file=...` if it isn't in the folder you start JMeter from. In real environments use your own password, and a validity that matches your test window.

On **each load generator**, from a folder that contains the test data (`data/users.csv`, `data/date_ranges.csv`):

```powershell
jmeter-server -Jserver.rmi.ssl.keystore.file=C:\jmetermi_keystore.jks `
  -Jserver.rmi.ssl.truststore.file=C:\jmetermi_keystore.jks -Jserver.rmi.localport=50000
```

On the **controller**:

```powershell
jmeter -n -t test-plans/10_claims_summary_load.jmx `
  -R 10.0.0.11,10.0.0.12,10.0.0.13 `
  -Jserver.rmi.ssl.keystore.file=C:\jmetermi_keystore.jks -Jserver.rmi.ssl.truststore.file=C:\jmetermi_keystore.jks `
  -Gusers=100 -Grampup=300 -Gduration=1800 -Ghost=app.test.internal `
  -l results/distributed.jtl -e -o results/distributed-report -X
```

| Option | Meaning |
|---|---|
| `-R host1,host2` | Use these load generators (`-r` uses the `remote_hosts` property in `jmeter.properties` instead) |
| `-Gname=value` | Send a property to every load generator. A `-q` file or `-J` on the controller is **not** sent. |
| `-X` | Stop the `jmeter-server` processes when the test ends |

## Try it on one machine

You can practise with two `jmeter-server` processes on your own computer. It doesn't add capacity, but you see every moving part. Make two folders, `genA` and `genB`, copy `test-plans/data` into each (one per "machine"), and put `rmi_keystore.jks` in the repo folder.

```powershell
# Terminal 1, inside genA: load generator A on port 1099
jmeter-server -Jserver.rmi.ssl.keystore.file=<repo>mi_keystore.jks -Jserver.rmi.ssl.truststore.file=<repo>mi_keystore.jks -Djava.rmi.server.hostname=127.0.0.1

# Terminal 2, inside genB: load generator B on port 1100
jmeter-server -Jserver.rmi.ssl.keystore.file=<repo>mi_keystore.jks -Jserver.rmi.ssl.truststore.file=<repo>mi_keystore.jks -Djava.rmi.server.hostname=127.0.0.1 -Dserver_port=1100

# Terminal 3, in the repo folder: the controller
jmeter -n -t test-plans/10_claims_summary_load.jmx -R 127.0.0.1:1099,127.0.0.1:1100 `
  -Jserver.rmi.ssl.keystore.file=rmi_keystore.jks -Jserver.rmi.ssl.truststore.file=rmi_keystore.jks `
  -Gusers=3 -Grampup=3 -Gduration=30 -Gthink_min_ms=1000 -Gthink_range_ms=1000 `
  -l results/distributed.jtl -X
```

Each generator starts 3 threads, so **6 users** hit the mock. Thread names in the `.jtl` start with the generator's address (`127.0.0.1:1099-Analysts (steady load) 1-1`), so you can tell them apart.

### What happened when we tested this

We ran exactly this with JMeter 5.6.3 while building the repo, and it taught us two things:

1. **The first attempt ran zero samples.** The generators were started from a folder without `data/`, and their logs said `File date_ranges.csv must exist and be readable`. The controller only printed `summary = 0`. Lesson: when a distributed run produces nothing, **read the generators' `jmeter-server.log`**, not just the controller's output.
2. After giving each generator its own copy of `data/`, the run produced 160 samples from both generators with 0 errors, and `-X` shut both servers down at the end.

## Alternatives

- **Independent runs, merged afterwards.** Start the same non-GUI test on several machines at the same time, each with its own data slice, then combine the `.jtl` files and build one report with `jmeter -g`. No RMI, very robust.
- **Containers.** Run load generators as Docker containers or Kubernetes pods, which makes it easy to add and remove capacity.
- **Cloud load-testing services** that run JMeter plans for you (for example Azure Load Testing, BlazeMeter, or AWS's Distributed Load Testing solution). Useful when you need a lot of load from several regions.

## Check yourself

1. You run with `-R gen1,gen2,gen3` and `-Gusers=200`. How many virtual users hit the system?
2. The controller says the test started, but the generators log `FileNotFoundException: users.csv`. Why?

<details><summary>Answers</summary>

1. 600: each generator runs the full 200.
2. CSV files are read on the generators. Copy the data file to each generator at the path the plan expects.
</details>

**Next:** [12 · CI integration with GitHub Actions](12-ci-with-github-actions.md)
