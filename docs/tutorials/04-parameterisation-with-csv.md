# 04 · Parameterisation with CSV

> **Goal:** feed each virtual user different data from a CSV file so the test behaves like many real users, not one user many times.
>
> **Script:** `test-plans/04_csv_parameterisation.jmx` · **Data:** `test-plans/data/users.csv`, `test-plans/data/date_ranges.csv`

## Why parameterise

If 300 threads all log in as the same user and ask for the same report:

- caches make the system look faster than it really is,
- session or locking rules may reject parallel logins,
- you only test one path through the data.

Parameterisation replaces hard-coded values with variables that change per user and per iteration.

## The data files

`users.csv` (50 synthetic analysts, all with the test-only password `learn-jmeter`):

```
username,password,providerId
analyst01,learn-jmeter,P1001
analyst02,learn-jmeter,P1002
...
```

`date_ranges.csv`:

```
from,to,rangeLabel
2026-01-01,2026-01-31,Jan 2026
2026-01-01,2026-03-31,Q1 2026
...
```

These are synthetic. In a healthcare project, never put real PHI or production credentials in a test data file. Use synthetic or approved masked data.

## CSV Data Set Config settings

| Setting | Value in plan 04 | Why |
|---|---|---|
| Filename | `data/users.csv` | Relative paths are resolved from the `.jmx` file's folder. |
| Variable names | *(empty)* | Empty means "read them from the first line". |
| Ignore first line | False | Only set True when you *do* type variable names yourself. |
| Recycle on EOF | True | Start again at the top when the file runs out. |
| Stop thread on EOF | False | Set True (with Recycle False) to use each row exactly once, as the negative tests in plan 06 do. |
| Sharing mode | All threads | Each new line goes to the next thread that asks, so every user gets different data. |

How it advances: each thread reads the **next line at the start of each iteration**. With 5 threads and 4 loops, plan 04 uses 20 rows.

## Using the variables

```
POST /api/auth/login
{"username":"${username}","password":"${password}"}

GET /api/reports/claims-summary?providerId=${providerId}&from=${from}&to=${to}
```

The plan also shows a few useful built-in functions:

| Function | Example | Gives |
|---|---|---|
| `${__P(name,default)}` | `${__P(users,5)}` | A property from `-Jusers=50`, or the default |
| `${__UUID()}` | `X-Request-Id: ${__UUID()}` | A random UUID (good for tracing requests in server logs) |
| `${__Random(1,100)}` | | A random number |
| `${__threadNum}` | | The current thread's number |
| `${__time(yyyy-MM-dd)}` | | The current date or time, formatted |
| `${__RandomString(8,abcdef)}` | | A random string |

## Run it

```powershell
jmeter -n -t test-plans/04_csv_parameterisation.jmx -Jusers=5 -Jloops=4 -l results/04.jtl
python scripts/jtl_summary.py results/04.jtl
```

In the GUI, enable View Results Tree and look at each request body: every one uses a different analyst.

## Sizing your data

Have at least as many unique rows as you need. For a 1-hour load with 300 users and 30-second sessions, that is a lot of logins. If each user should log in once, give each thread its own row (a bigger file, or *Sharing mode: Current thread group*), or log in once per thread with a **Once Only Controller**.

## Check yourself

1. What is the difference between parameterisation and correlation?
2. You want each row used exactly once and the thread to stop when the file ends. Which settings?

<details><summary>Answers</summary>

1. Parameterisation feeds input data you control (from a file). Correlation captures dynamic values the server generates (tokens, IDs) and passes them to later requests.
2. Recycle on EOF = False, Stop thread on EOF = True.
</details>

**Next:** [05 · Correlation](05-correlation.md)
