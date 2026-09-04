# -*- coding: utf-8 -*-
"""
NOTIFIER - Email (Gmail SMTP) + Windows desktop toast.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    EMAIL_TO, EMAIL_FROM, SMTP_HOST, SMTP_PORT, SMTP_PASSWORD,
    ENABLE_EMAIL, ENABLE_DESKTOP_TOAST,
)

log = logging.getLogger(__name__)


# ---------------- EMAIL ----------------
def send_email(subject: str, body_html: str) -> bool:
    if not ENABLE_EMAIL:
        return False
    if not SMTP_PASSWORD or SMTP_PASSWORD.startswith("PASTE_"):
        log.warning("SMTP_PASSWORD not configured - skipping email")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls()
            s.login(EMAIL_FROM, SMTP_PASSWORD)
            s.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        log.info("Email sent: %s", subject)
        return True
    except Exception as e:
        log.error("Email send failed: %s", e)
        return False


# ---------------- DESKTOP TOAST ----------------
def send_toast(title: str, message: str, url: str | None = None,
               tag: str | None = None) -> bool:
    """Send Windows toast. Uses unique tag/group per notification so Windows
    doesn't dedupe/replace when multiple arrive close together."""
    if not ENABLE_DESKTOP_TOAST:
        return False
    try:
        from winotify import Notification, audio
        import hashlib, time
        # Unique tag ensures each notification is a NEW toast (not replacement)
        if not tag:
            seed = f"{title}{message}{time.time_ns()}"
            tag = hashlib.md5(seed.encode()).hexdigest()[:16]
        toast = Notification(
            app_id="JobMonitor",
            title=title,
            msg=message,
            duration="long",
        )
        toast.set_audio(audio.Default, loop=False)
        if url:
            # Label chosen dynamically: "View report" for HTML files,
            # "Apply now" for direct job URLs (kept for potential future use).
            label = "View report" if url.lower().endswith(".html") or "file:///" in url.lower() else "Apply now"
            toast.add_actions(label=label, launch=url)
        # Force unique identity per toast
        try:
            toast.tag = tag
            toast.group = "jobmatches"
        except Exception:
            pass
        toast.show()
        return True
    except ImportError:
        log.warning("winotify not installed - install via: pip install winotify")
        return False
    except Exception as e:
        log.error("Toast failed: %s", e)
        return False


# ---------------- FORMATTED JOB NOTIFICATION ----------------
def notify_job_match(company, title, location, url, score, matched_kw):
    """Send both email + desktop toast for a matched job."""

    # --- Desktop toast (short) ---
    toast_title = f"[{score}] {company} - {title}"
    toast_msg   = f"{location}\n{matched_kw[:120]}"
    send_toast(toast_title, toast_msg, url)

    # --- Email (rich HTML) ---
    color = "#22c55e" if score >= 80 else ("#f59e0b" if score >= 70 else "#6b7280")
    body = f"""
    <html><body style="font-family:Segoe UI,Arial,sans-serif;
                       background:#1a1a1a;color:#e5e7eb;padding:20px;">
      <div style="max-width:640px;margin:auto;background:#111;border-radius:8px;
                  padding:24px;border:1px solid #333;">
        <h2 style="margin:0 0 4px 0;color:#22d3ee;">{company}</h2>
        <h3 style="margin:0 0 16px 0;color:#fff;">{title}</h3>

        <div style="margin:16px 0;">
          <span style="display:inline-block;padding:6px 14px;background:{color};
                       color:#000;font-weight:bold;border-radius:4px;
                       font-family:JetBrains Mono,monospace;">
            SCORE {score}/100
          </span>
          <span style="margin-left:12px;color:#9ca3af;">📍 {location}</span>
        </div>

        <p style="color:#d1d5db;font-size:14px;line-height:1.6;">
          <strong style="color:#22d3ee;">Matched keywords:</strong><br>
          <code style="color:#a3e635;">{matched_kw}</code>
        </p>

        <a href="{url}"
           style="display:inline-block;margin-top:20px;padding:12px 24px;
                  background:#22d3ee;color:#000;font-weight:bold;
                  text-decoration:none;border-radius:6px;">
          Apply Now &rarr;
        </a>

        <p style="margin-top:24px;color:#6b7280;font-size:11px;">
          Auto-sent by JobMonitor - Diego Lombardi
        </p>
      </div>
    </body></html>
    """
    subject = f"[JOB {score}] {company} - {title} ({location})"
    send_email(subject, body)


# --- Self-test ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing desktop toast...")
    send_toast("JobMonitor Test",
               "If you see this popup, desktop notifications work!",
               "https://example.com")
    print("Done. Check the notification area.")
