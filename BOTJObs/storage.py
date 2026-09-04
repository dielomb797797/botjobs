# -*- coding: utf-8 -*-
"""
STORAGE - SQLite persistence layer.
Keeps track of seen jobs to avoid duplicate notifications.
"""
import sqlite3
import hashlib
import os
from datetime import datetime
from config import DB_PATH


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create schema on first run."""
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id       TEXT PRIMARY KEY,
            company      TEXT NOT NULL,
            title        TEXT NOT NULL,
            location     TEXT,
            url          TEXT NOT NULL,
            score        INTEGER,
            matched_kw   TEXT,
            first_seen   TEXT NOT NULL,
            notified_at  TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_company ON jobs(company);
        CREATE INDEX IF NOT EXISTS idx_score   ON jobs(score);

        CREATE TABLE IF NOT EXISTS run_log (
            run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at   TEXT NOT NULL,
            finished_at  TEXT,
            sites_ok     INTEGER,
            sites_fail   INTEGER,
            new_jobs     INTEGER,
            high_matches INTEGER,
            notes        TEXT
        );
        """)


def make_job_id(company: str, title: str, url: str) -> str:
    """Deterministic ID from company+title+url (stable across runs)."""
    raw = f"{company.lower().strip()}|{title.lower().strip()}|{url.strip()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def is_new_job(job_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return row is None


def save_job(job_id, company, title, location, url, score, matched_kw):
    """Insert new job (idempotent)."""
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO jobs
            (job_id, company, title, location, url, score, matched_kw, first_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, company, title, location, url, score, matched_kw, now))


def mark_notified(job_id: str):
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute("UPDATE jobs SET notified_at = ? WHERE job_id = ?", (now, job_id))


def start_run() -> int:
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute("INSERT INTO run_log (started_at) VALUES (?)", (now,))
        return cur.lastrowid


def finish_run(run_id: int, sites_ok, sites_fail, new_jobs, high_matches, notes=""):
    now = datetime.utcnow().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute("""
            UPDATE run_log SET finished_at=?, sites_ok=?, sites_fail=?,
                               new_jobs=?, high_matches=?, notes=?
            WHERE run_id=?
        """, (now, sites_ok, sites_fail, new_jobs, high_matches, notes, run_id))


def recent_high_matches(limit: int = 20):
    with _connect() as conn:
        return conn.execute("""
            SELECT company, title, location, url, score, matched_kw, first_seen
            FROM jobs
            WHERE score >= 70
            ORDER BY first_seen DESC
            LIMIT ?
        """, (limit,)).fetchall()
