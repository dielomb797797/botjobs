# -*- coding: utf-8 -*-
"""
CONFIG - Central configuration for the Job Monitor.
Edit this file to change email, keywords, sites, thresholds.
"""

# ==========================================================
# NOTIFICATION SETTINGS - DIGEST MODE ONLY
# ==========================================================
# NO real-time popups. Instead: 1 desktop notification per day at DIGEST_TIME
# with a link to a HTML report showing all matches found that day.

ENABLE_EMAIL          = False   # disabled (kept in code in case wanted later)
ENABLE_DESKTOP_TOAST  = True    # <<< notifications ACTIVE

# Email settings (unused while ENABLE_EMAIL=False)
EMAIL_TO       = "diego.lomba79@gmail.com"
EMAIL_FROM     = "diego.lomba79@gmail.com"
SMTP_HOST      = "smtp.gmail.com"
SMTP_PORT      = 587
SMTP_PASSWORD  = ""

# ==========================================================
# SCHEDULER
# ==========================================================
CHECK_INTERVAL_MINUTES = 30         # silent scan cadence (every 30 min)
DAILY_DIGEST_HOUR      = 19         # 19:00 local time
DAILY_DIGEST_MINUTE    = 0
DIGEST_INCLUDE_MEDIUM  = True       # include score 50-69 in the report
DIGEST_SILENT_IF_EMPTY = True       # if 0 matches today, do NOT show popup

# --- INSTANT NOTIFICATIONS (real-time popup on new match) ---
INSTANT_NOTIFY_ENABLED   = True     # popup as soon as a new match is found
INSTANT_NOTIFY_MIN_SCORE = 50       # notify for EVERY match (HIGH + MEDIUM)
INSTANT_NOTIFY_MAX_PER_SCAN = 25    # generous cap - safety only

# ==========================================================
# SCORING THRESHOLDS
# ==========================================================
SCORE_THRESHOLD_HIGH   = 70      # immediate notification
SCORE_THRESHOLD_MEDIUM = 50      # daily digest
# below 50 -> ignored

# ==========================================================
# TARGET PROFILE (Diego Lombardi - Solutions/Integration/TAM)
# ==========================================================

TARGET_LOCATIONS = [
    "amsterdam", "madrid",
    "netherlands", "spain",
    "remote eu", "remote europe",
]

TARGET_TITLES = [
    "solutions engineer", "associate solutions engineer",
    "implementation specialist", "implementation consultant",
    "integration engineer", "integration specialist",
    "technical account manager", "tam",
    "technical onboarding", "onboarding specialist",
    "product operations", "product ops",
    "technical operations", "operations automation",
    "solutions architect associate", "customer solutions engineer",
    "deployment engineer", "deployment specialist",
    # Technical pre-sales (Sales Engineer = technical role, NOT pure sales)
    "sales engineer", "presales engineer", "pre-sales engineer",
    "customer engineer",
    # Strategy & Operations family (Diego will manually filter these)
    "strategy and operations", "strategy & operations", "strategy and ops",
    "strategy & ops", "s&o",
    "business operations", "business ops",
    "operations analyst", "operations manager", "operations associate",
    "operations specialist", "operations consultant",
    "strategy analyst", "strategy associate", "strategy manager",
    "strategy consultant",
    "graduate programme", "graduate program", "graduate rotation",
    "rotational programme", "rotational program",
]

CORE_DUTIES_KEYWORDS = [
    "api", "rest api", "integration", "onboarding",
    "saas", "b2b", "workflow", "automation",
    "troubleshoot", "root cause", "postman", "logs",
    "llm", "ai tooling", "process optimization",
    "sop", "diagnostic", "cross-functional",
    "product engineering", "technical stakeholder",
]

SKILL_KEYWORDS = [
    "python", "sql", "json", "rest", "postman",
    "iot", "data analytics", "excel", "matlab",
    "linux", "git", "docker",
]

SENIORITY_ACCEPTED = [
    "entry", "junior", "associate", "graduate", "grad",
    "mid", "mid-level", "intermediate",
    "0-2 years", "1-3 years", "0-3 years",
]

# Title-prefix exclusions - if job title STARTS with these words, reject it.
# (More precise than adding to general EXCLUSION_KEYWORDS, since these words
# often appear in job descriptions legitimately - e.g. "reporting to a senior
# manager" should NOT block a valid entry-level role.)
TITLE_PREFIX_EXCLUSIONS = [
    "senior ", "sr. ", "sr ",
    "staff ",
    "principal ",
    "lead ",
    "head of ", "director ", "vp ", "vice president",
    "chief ",
]

# ==========================================================
# EXCLUSION - kill switch (any match => score = 0)
# ==========================================================
EXCLUSION_KEYWORDS = [
    "24/7", "shift work", "rotational shift", "rotating shift",
    "night shift", "weekend shift", "on-call", "on call duty",
    "account executive", "business development representative",
    "outbound prospecting", "cold calling", "cold-calling",
    "closing quotas", "quota carrying", "quota-carrying",
    "sdr", "bdr",
    # Pure economic/commercial sales (NOT Sales Engineer - which is technical)
    "sales representative", "sales development representative",
    "inside sales", "field sales", "sales director",
    "commercial intern",
    # NOTE: NOT excluding "account manager" alone because "technical account manager"
    # contains it. Pure "account manager" roles will naturally score below threshold
    # (no title match => max 60 pts).
    "senior ml engineer", "staff engineer", "staff software",
    "principal engineer", "deep learning research",
    "fpga", "rtl design", "microchip design", "low-latency c++",
    "legal compliance", "hr business partner", "payroll specialist",
    "recruiter", "talent acquisition",
]

# ==========================================================
# TARGET SITES
# ==========================================================
SITES = [
    ("Mollie",  "https://jobs.mollie.com/",                 "mollie"),
    ("Booking", "https://careers.booking.com/",             "booking"),
    ("Miro",    "https://miro.com/careers/open-positions/", "miro"),
]

# ==========================================================
# HTTP SETTINGS
# ==========================================================
HTTP_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ==========================================================
# PATHS
# ==========================================================
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "jobs.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "monitor.log")
