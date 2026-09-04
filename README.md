# 🤖 BOTJObs — Automated Job Monitoring Bot

> Tracks 25 company career sites in real-time and delivers instant alerts for matching roles.

## What it does

- Monitors **25 ATS platforms** every ~30 minutes (Greenhouse, Ashby, SmartRecruiters, Lever, Recruitee, Personio + 6 anti-bot sites via Playwright)
- Scores each job **0–100** based on title, location, seniority, duties and skills
- Sends **instant desktop notifications** for matches ≥ 70 with a direct "Apply Now" link
- Generates a **daily HTML report** showing all active matches with NEW badges for fresh discoveries
- Runs silently in the background via Windows Task Scheduler — starts at login, auto-restarts on crash

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| API scraping | REST APIs (Greenhouse, Ashby, SmartRecruiters, Lever, Recruitee, Personio) |
| Anti-bot scraping | Playwright (headless browser) |
| Notifications | Windows Toast Notifications |
| Scheduling | Windows Task Scheduler |
| Data persistence | SQLite |
| Reporting | HTML/CSS generated report |

## Features

- ✅ **Scoring engine** — weighted algorithm (title 40%, location 20%, seniority 15%, duties 15%, skills 10%)
- ✅ **Hard filters** — auto-excludes Senior/Lead/Director titles, night shifts, cold-sales roles
- ✅ **Hybrid notification strategy** — instant popup per match + daily 19:00 digest
- ✅ **No duplicate alerts** — already-seen jobs are never re-notified
- ✅ **Modular config** — all thresholds adjustable in `config.py` without code edits

## Project Structure
