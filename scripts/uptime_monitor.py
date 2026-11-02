"""Polls /health and logs results; prints uptime % (SCMS-NF-002 target: 99.5%).

Run:    python scripts/uptime_monitor.py --url http://127.0.0.1:5000/health --interval 30
Report: python scripts/uptime_monitor.py --report
"""
import argparse
import csv
import os
import time
import urllib.request
from datetime import datetime, timezone

LOG = "logs/uptime.csv"
TARGET = 99.5


def check(url):
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            ok = resp.status == 200
    except Exception:
        ok = False
    return ok, int((time.time() - start) * 1000)


def report():
    if not os.path.exists(LOG):
        print("No log yet.")
        return
    with open(LOG, newline="") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    up = sum(1 for r in rows if r["up"] == "1")
    pct = 100.0 * up / total if total else 0.0
    print(f"Checks: {total}  Up: {up}  Down: {total - up}")
    print(f"Uptime: {pct:.3f}%  (target {TARGET}%)  ->  "
          f"{'PASS' if pct >= TARGET else 'FAIL'}")


def monitor(url, interval, duration):
    os.makedirs("logs", exist_ok=True)
    new = not os.path.exists(LOG)
    end = time.time() + duration if duration else None
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "up", "latency_ms"])
        while end is None or time.time() < end:
            ok, ms = check(url)
            w.writerow([datetime.now(timezone.utc).isoformat(), int(ok), ms])
            f.flush()
            print(f"{'UP  ' if ok else 'DOWN'} {ms} ms")
            time.sleep(interval)
    report()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:5000/health")
    p.add_argument("--interval", type=int, default=30)
    p.add_argument("--duration", type=int, default=0, help="seconds; 0 = run forever")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    report() if a.report else monitor(a.url, a.interval, a.duration)