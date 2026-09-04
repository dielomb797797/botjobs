# scerring - Job Monitor

Automated career-page monitor for **Diego Lombardi**.
Scans a list of target companies, scores each open position against a target
profile (Solutions Engineer / Integration / TAM roles in Amsterdam/Madrid),
and sends an **immediate email + desktop notification** on high matches.

---

## Quick start

```powershell
# 1. Install dependencies (one time)
python -m pip install -r requirements.txt

# 2. Configure Gmail App Password
#    -> https://myaccount.google.com/apppasswords
#    -> paste the 16-char password in config.py -> SMTP_PASSWORD

# 3. Test notifications
python main.py test

# 4. Run one scan
python main.py once

# 5. Run in loop (every 30 min)
python main.py loop
```

Or use the PowerShell launcher:
```powershell
.\avvia_monitor.ps1 once
.\avvia_monitor.ps1 loop
.\avvia_monitor.ps1 test
```

---

## Project structure

```
scerring/
├── config.py          # Central config: email, keywords, sites, thresholds
├── main.py            # Entry point
├── matcher.py         # 0-100 scoring engine
├── notifier.py        # Email (Gmail SMTP) + Windows toast
├── storage.py         # SQLite dedup
├── scrapers/
│   ├── base.py        # HTTP utilities
│   └── mollie.py      # First scraper (Greenhouse API)
├── data/jobs.db       # SQLite (auto-created)
├── logs/monitor.log   # Runtime log
└── avvia_monitor.ps1  # PowerShell launcher
```

---

## How the scoring works

- **Title match** (40 pts) - job title contains one of TARGET_TITLES
- **Location** (20 pts) - HARD FILTER: must be Amsterdam / Madrid / NL / ES
- **Seniority** (15 pts) - entry / associate / mid
- **Duties** (15 pts) - API, integration, onboarding, automation, LLM...
- **Skills** (10 pts) - Python, REST, JSON, Postman, IoT...

**Kill switches (score -> 0):** 24/7, shift, night, AE, BDR, cold calling,
staff/senior IC, FPGA, RTL, HR, payroll, recruiter.

- Score >= 70 -> **immediate notification** (email + toast)
- Score 50-69 -> logged only (future: daily digest)
- Score <  50 -> ignored
```
