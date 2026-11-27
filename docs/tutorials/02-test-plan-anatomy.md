# 02 · Test plan anatomy

> **Goal:** know what each kind of element in a JMeter test plan does, and the order JMeter runs them in.
>
> **Script:** `test-plans/02_test_plan_anatomy.jmx`

## The tree

Open the script in the GUI (`jmeter -t test-plans/02_test_plan_anatomy.jmx`). You will see:

```
Test Plan: 02 Test plan anatomy          (User Defined Variables: HOST, PORT, USERS ...)
└── Thread Group: browsing users          (3 users, 3 s ramp-up, 5 loops)
    ├── HTTP Request Defaults            config element: host, port, protocol, timeouts
    ├── HTTP Header Manager              config element: Content-Type, Accept
    ├── HTTP Cookie Manager              config element: stores cookies per user
    ├── GET /health                      sampler
    │   └── Assert status 200            assertion
    ├── GET /api/providers               sampler
    │   ├── Assert status 200
    │   └── Body lists providers
    └── Think time (1-2 s)               Flow Control Action holding a Uniform Random Timer
View Results Tree / Summary Report / Aggregate Report   listeners
```

## The element types

| Type | What it does | Examples |
|---|---|---|
| **Test Plan** | The root. Holds global variables and settings. | User Defined Variables |
| **Thread Group** | A group of virtual users and how they start and loop. | Thread Group, setUp/tearDown Thread Group |
| **Sampler** | Sends a request and records a result (a *sample*). | HTTP Request, JDBC Request, JSR223 Sampler |
| **Config element** | Settings and data that samplers use. | HTTP Request Defaults, Header Manager, Cookie Manager, CSV Data Set Config |
| **Pre-processor** | Runs just before a sampler. | JSR223 PreProcessor, User Parameters |
| **Post-processor** | Runs just after a sampler, usually to extract data. | JSON Extractor, Regular Expression Extractor |
| **Assertion** | Checks a response and marks the sample failed if it is wrong. | Response Assertion, JSON Assertion, Duration Assertion |
| **Timer** | Adds a delay before a sampler. | Constant Timer, Uniform Random Timer, Constant Throughput Timer |
| **Logic controller** | Decides which samplers run and how often. | Transaction, If, Loop, While, Switch, Once Only |
| **Listener** | Collects and shows results. | View Results Tree, Summary Report, Aggregate Report, Backend Listener |

## Thread Group settings

| Setting | Meaning |
|---|---|
| **Number of threads (users)** | How many virtual users. Each thread runs the whole tree independently. |
| **Ramp-up period** | Seconds to start all threads. 100 threads with 50 s ramp-up = 2 new users per second. |
| **Loop count** | Iterations per user. *Infinite* plus a duration is the normal choice for load tests. |
| **Specify thread lifetime → Duration** | How long the group runs, in seconds, however many loops that takes. |
| **Startup delay** | Seconds to wait before this group starts (used for the spike group in plan 10). |
| **Action after a sampler error** | Continue, start next loop, stop thread, stop test. *Continue* is usual for load tests. |
| **Same user on each iteration** | Keep cookies and cache between iterations (on by default). |

**Ramp-up vs duration** is a classic interview question: ramp-up is how long it takes to *start* the users; duration is how long the group *runs in total*, including the ramp-up.

## Scope: where you put an element matters

Config elements, timers, assertions, pre- and post-processors apply to every sampler **at their level and below**:

- An assertion *under* a sampler checks only that sampler.
- An assertion at *Thread Group level* checks every sampler in the group.
- HTTP Request Defaults at Test Plan or Thread Group level gives every HTTP sampler the same host and port, so you can switch environments with one property.

## Execution order for each sampler

1. Configuration elements
2. Pre-processors
3. Timers
4. **Sampler**
5. Post-processors (only if the sample has a result)
6. Assertions
7. Listeners

Remember that timers run *before* the sampler they are attached to. That is why plan 02 puts its think time on a separate Flow Control Action: the pause happens *between* requests without being added to any request's response time.

## Variables and properties

- **Variables** (`${HOST}`) belong to one thread. User Defined Variables are read once at the start.
- **Properties** (`${__P(users,3)}`) belong to the whole JMeter process and can be set on the command line with `-J`.

Plan 02 reads all its settings through properties with defaults, so you can change the load without editing the file:

```powershell
jmeter -n -t test-plans/02_test_plan_anatomy.jmx -Jusers=10 -Jloops=20 -l results/02.jtl
```

## Listeners: GUI only

Listeners are useful while you build a script and harmful during a real test. In plans 10 and later they are **disabled**, and results go to the `.jtl` file with `-l`. You can open a `.jtl` file in any listener later (Browse... button) or turn it into an HTML report (Tutorial 10).

## Exercise

1. Run plan 02 in the GUI, then open **Aggregate Report**. Find the average, p90 and throughput for `GET /api/providers`.
2. Change ramp-up to 0 and users to 20. What happens to response times?
3. Move *Assert status 200* from `GET /health` up to the Thread Group. How many samples does it now check?

**Next:** [03 · Recording vs scripting](03-recording-vs-scripting.md)
