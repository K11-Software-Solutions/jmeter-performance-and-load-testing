#!/usr/bin/env python3
"""Run every tutorial test plan in non-GUI mode and check that no sample failed.

Start the mock API first:   node mock-server/server.js
Then run:                   python scripts/run_tutorials.py
Only some plans:            python scripts/run_tutorials.py 04 05

JMeter is found from the JMETER_HOME environment variable, or from `jmeter` on your PATH.
Each run writes results/tutorials/<plan>.jtl and <plan>.log.
"""
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANS = os.path.join(ROOT, "test-plans")
OUT = os.path.join(ROOT, "results", "tutorials")

# Plans run by default, with the extra properties each one needs to stay short.
DEFAULT = {
    "01_hello_jmeter.jmx": [],
    "02_test_plan_anatomy.jmx": [],
    "03_recorded_portal_flow.jmx": [],
    "04_csv_parameterisation.jmx": [],
    "05_correlation.jmx": [],
    "06_assertions.jmx": [],
    "07_timers.jmx": ["-Jtg_duration=15"],
    "08_logic_controllers.jmx": [],
    "09_jsr223_groovy.jmx": [],
    "10_claims_summary_load.jmx": ["-q", os.path.join(PLANS, "profiles", "smoke.properties"), "-Jduration=30"],
}


def jmeter_cmd():
    home = os.environ.get("JMETER_HOME")
    exe = "jmeter.bat" if os.name == "nt" else "jmeter"
    if home:
        return os.path.join(home, "bin", exe)
    found = shutil.which(exe) or shutil.which("jmeter")
    if not found:
        sys.exit("JMeter not found. Set JMETER_HOME or put JMeter's bin folder on your PATH.")
    return found


def main():
    wanted = sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    jm = jmeter_cmd()
    results = []
    for plan, extra in DEFAULT.items():
        if wanted and not any(plan.startswith(w) for w in wanted):
            continue
        name = plan[:-4]
        jtl = os.path.join(OUT, name + ".jtl")
        log = os.path.join(OUT, name + ".log")
        for f in (jtl, log):
            if os.path.exists(f):
                os.remove(f)
        cmd = [jm, "-n", "-t", os.path.join(PLANS, plan), "-l", jtl, "-j", log] + extra
        print("\n=== " + plan)
        t0 = time.time()
        rc = subprocess.call(cmd)
        summary_rc = subprocess.call([sys.executable, os.path.join(ROOT, "scripts", "jtl_summary.py"), jtl,
                                      "--fail-on-errors"])
        ok = rc == 0 and summary_rc == 0
        results.append((plan, ok, time.time() - t0))
    print("\n=== Result")
    for plan, ok, secs in results:
        print("{:<36} {:<5} {:>5.0f} s".format(plan, "PASS" if ok else "FAIL", secs))
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
