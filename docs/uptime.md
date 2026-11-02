# Availability: SCMS-NF-002 (99.5% uptime)

| Period | Allowed downtime at 99.5% |
|---|---|
| Per 30-day month | 3 h 36 min (216 min) |
| Per week | 50 min |
| Per day | 7 min 12 s |

## Monitoring
- Endpoint: `GET /health` returns 200 when the app and database are up, 503 when the database is down.
- External monitor: UptimeRobot or Better Stack, checking `/health` every 5 minutes with email alerts (needs a public URL; free tier is enough).
- Local/demo evidence: `scripts/uptime_monitor.py` logs each check to `logs/uptime.csv` and reports uptime %.

## Measuring
Uptime % = successful checks / total checks x 100 over a rolling 30 days.
Planned maintenance is excluded and must be announced in advance.

## How we meet the target
- Health checks with alerting, so outages are noticed in minutes.
- Run gunicorn with multiple workers behind nginx (see docs/deploy/nginx.conf), with automatic restart on crash.
- Database migrations are applied before restart to avoid downtime.