# -*- coding: utf-8 -*-
"""
DAILY DIGEST - Generates HTML report of all jobs found today and shows
a single desktop notification linking to it.

The report supports 3 states per job (localStorage, persisted across reports):
  - Applied     -> moves to "Applied Jobs" section (green)
  - Not a fit   -> moves to "Discarded" section (collapsed, gray)
  - Default     -> stays in HIGH/MEDIUM lists
"""
import os
import sqlite3
import hashlib
import logging
from datetime import datetime, date
from config import (DB_PATH, BASE_DIR, SCORE_THRESHOLD_HIGH, SCORE_THRESHOLD_MEDIUM,
                    DIGEST_INCLUDE_MEDIUM, DIGEST_SILENT_IF_EMPTY)
from notifier import send_toast

log = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(BASE_DIR, "data", "reports")


def get_todays_matches():
    """Return list of ALL active matches (score >= threshold), sorted by score desc.
    Each row has an is_new_today flag if first-seen today."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    today = date.today().isoformat()
    min_score = SCORE_THRESHOLD_MEDIUM if DIGEST_INCLUDE_MEDIUM else SCORE_THRESHOLD_HIGH
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT job_id, company, title, location, url, score, matched_kw, first_seen
            FROM jobs
            WHERE score >= ?
            ORDER BY score DESC, company ASC
        """, (min_score,)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["is_new_today"] = d["first_seen"].startswith(today)
        result.append(d)
    return result


def build_html_report(matches, out_path):
    """Generate a self-contained HTML report with 3-state tracking."""
    today_str = date.today().strftime("%A, %d %B %Y")
    high = [m for m in matches if m["score"] >= SCORE_THRESHOLD_HIGH]
    med  = [m for m in matches if m["score"] < SCORE_THRESHOLD_HIGH]

    def card(m):
        color = "#22c55e" if m["score"] >= 85 else ("#84cc16" if m["score"] >= 70 else "#f59e0b")
        kw_html = m.get("matched_kw","").replace("|","<br>")
        jid = m["job_id"]
        new_badge = '<span class="new-badge">NEW</span>' if m.get("is_new_today") else ""
        return f"""
        <div class="job-card" data-job-id="{jid}">
          <div class="job-header">
            <div style="flex:1;">
              <div class="company">{m["company"]} {new_badge}</div>
              <div class="title">{m["title"]}</div>
              <div class="location">📍 {m["location"] or "-"}</div>
            </div>
            <div class="score" style="background:{color};">{m["score"]}</div>
          </div>
          <div class="matched">
            <span class="matched-label">Matched:</span> {kw_html}
          </div>
          <div class="actions">
            <a class="apply-btn" href="{m["url"]}" target="_blank"
               onclick="markPending('{jid}')">Apply Now →</a>
            <button class="applied-btn" onclick="toggleApplied('{jid}')"
                    id="btn-applied-{jid}">✓ Mark as Applied</button>
            <button class="discard-btn" onclick="toggleDiscarded('{jid}')"
                    id="btn-discard-{jid}">✕ Not a fit</button>
          </div>
        </div>
        """

    all_cards_high = "".join(card(m) for m in high)
    all_cards_med  = "".join(card(m) for m in med)

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Job Monitor · Daily Digest · {today_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #1a1a1a; color: #e5e7eb; padding: 32px 20px;
  }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  h1 {{ color: #22d3ee; font-size: 28px; margin-bottom: 4px; }}
  .subtitle {{ color: #9ca3af; margin-bottom: 24px; font-size: 14px; }}
  .stats {{
    display: flex; gap: 16px; margin-bottom: 32px;
    padding: 16px; background: #111; border-radius: 8px; border: 1px solid #333;
  }}
  .stat {{ flex: 1; text-align: center; cursor: default; }}
  .stat-num {{ font-size: 32px; font-weight: bold; color: #22d3ee; }}
  .stat-lbl {{ color: #9ca3af; font-size: 12px; text-transform: uppercase; }}
  .stat.applied .stat-num {{ color: #a3e635; }}
  .stat.discarded .stat-num {{ color: #6b7280; }}
  h2 {{ color: #fff; margin: 24px 0 16px 0; font-size: 20px;
        border-bottom: 1px solid #333; padding-bottom: 8px;
        cursor: pointer; user-select: none; }}
  h2 .badge {{ background: #22d3ee; color: #000; padding: 2px 8px;
               border-radius: 4px; font-size: 14px; margin-left: 8px; }}
  h2.applied .badge {{ background: #a3e635; }}
  h2.discarded .badge {{ background: #6b7280; }}
  h2 .toggle-icon {{ float: right; font-size: 14px; color: #6b7280; }}

  .job-card {{
    background: #111; border: 1px solid #333; border-radius: 8px;
    padding: 20px; margin-bottom: 12px; transition: all 0.2s;
  }}
  .job-card.applied {{
    opacity: 0.6; background: #0a1f0a; border-color: #365314;
  }}
  .job-card.applied .title {{ text-decoration: line-through; }}
  .job-card.discarded {{
    opacity: 0.4; background: #1a1a1a; border-color: #333;
  }}
  .job-card.discarded .title {{
    text-decoration: line-through; color: #6b7280;
  }}
  .job-card.discarded .matched {{ display: none; }}

  .job-header {{ display: flex; justify-content: space-between;
                 align-items: start; margin-bottom: 12px; gap: 12px; }}
  .company {{ color: #22d3ee; font-size: 14px; font-weight: bold; }}
  .new-badge {{
    display: inline-block; background: #ef4444; color: #fff;
    font-size: 10px; font-weight: 800; padding: 2px 6px;
    border-radius: 3px; margin-left: 8px; vertical-align: middle;
    letter-spacing: 0.5px;
  }}
  .title {{ color: #fff; font-size: 17px; font-weight: 600; margin: 4px 0; }}
  .location {{ color: #9ca3af; font-size: 13px; }}
  .score {{
    color: #000; font-weight: bold; padding: 8px 14px; border-radius: 4px;
    font-family: 'JetBrains Mono', monospace; font-size: 16px;
    min-width: 60px; text-align: center;
  }}
  .matched {{ color: #a3e635; font-size: 12px; margin: 12px 0;
              padding: 8px 12px; background: #0a0a0a; border-radius: 4px;
              font-family: monospace; }}
  .matched-label {{ color: #22d3ee; }}
  .actions {{ display: flex; gap: 10px; align-items: center;
              margin-top: 12px; flex-wrap: wrap; }}
  .apply-btn {{
    display: inline-block; padding: 10px 20px;
    background: #22d3ee; color: #000; font-weight: bold;
    text-decoration: none; border-radius: 6px;
  }}
  .apply-btn:hover {{ background: #67e8f9; }}
  .applied-btn {{
    padding: 10px 16px;
    background: transparent; color: #a3e635; font-weight: 600;
    border: 1px solid #a3e635; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-family: inherit;
  }}
  .applied-btn:hover {{ background: #a3e635; color: #000; }}
  .applied-btn.done {{ background: #a3e635; color: #000; }}
  .applied-btn.done::before {{ content: "✅ "; }}

  .discard-btn {{
    padding: 10px 16px;
    background: transparent; color: #ef4444; font-weight: 600;
    border: 1px solid #ef4444; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-family: inherit;
  }}
  .discard-btn:hover {{ background: #ef4444; color: #fff; }}
  .discard-btn.done {{ background: #6b7280; color: #fff; border-color: #6b7280; }}
  .discard-btn.done::before {{ content: "↩ "; }}

  .empty {{ color: #6b7280; text-align: center; padding: 40px; font-style: italic; }}
  .footer {{ color: #6b7280; text-align: center; margin-top: 40px;
             font-size: 11px; padding-top: 20px; border-top: 1px solid #333; }}
  .reset-btn {{
    background: transparent; color: #6b7280; border: 1px solid #444;
    padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px;
    margin-left: 12px;
  }}
  .reset-btn:hover {{ color: #ef4444; border-color: #ef4444; }}
  .section-content.collapsed {{ display: none; }}
</style></head><body>

<div class="container">
  <h1>Job Monitor · Daily Digest</h1>
  <div class="subtitle">{today_str} · Diego Lombardi</div>

  <div class="stats">
    <div class="stat"><div class="stat-num">{len(matches)}</div>
                       <div class="stat-lbl">Total matches</div></div>
    <div class="stat"><div class="stat-num">{len(high)}</div>
                       <div class="stat-lbl">High (≥70)</div></div>
    <div class="stat"><div class="stat-num">{len(med)}</div>
                       <div class="stat-lbl">Medium (50-69)</div></div>
    <div class="stat applied">
      <div class="stat-num" id="applied-count">0</div>
      <div class="stat-lbl">Applied
        <button class="reset-btn" onclick="resetState('applied')">Reset</button>
      </div>
    </div>
    <div class="stat discarded">
      <div class="stat-num" id="discarded-count">0</div>
      <div class="stat-lbl">Discarded
        <button class="reset-btn" onclick="resetState('discarded')">Reset</button>
      </div>
    </div>
  </div>

  <h2 class="applied" id="applied-section" style="display:none;"
      onclick="toggleSection('applied-list', this)">
    ✅ Applied Jobs <span class="badge" id="applied-badge">0</span>
    <span class="toggle-icon">▼</span>
  </h2>
  <div id="applied-list" class="section-content"></div>

  <h2 id="high-header" onclick="toggleSection('high-list', this)">
    🎯 High Matches <span class="badge">{len(high)}</span>
    <span class="toggle-icon">▼</span>
  </h2>
  <div id="high-list" class="section-content">
    {all_cards_high if high else '<div class="empty">No high matches today.</div>'}
  </div>

  <h2 id="med-header" onclick="toggleSection('med-list', this)">
    🟡 Medium Matches <span class="badge">{len(med)}</span>
    <span class="toggle-icon">▼</span>
  </h2>
  <div id="med-list" class="section-content">
    {all_cards_med if med else '<div class="empty">No medium matches today.</div>'}
  </div>

  <h2 class="discarded" id="discarded-section" style="display:none;"
      onclick="toggleSection('discarded-list', this)">
    ✕ Discarded / Not a fit <span class="badge" id="discarded-badge">0</span>
    <span class="toggle-icon">▶</span>
  </h2>
  <div id="discarded-list" class="section-content collapsed"></div>

  <div class="footer">Generated by JobMonitor · BOTJObs · {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
</div>

<script>
  // ==================== State (localStorage) ====================
  const STORE_APPLIED   = "jobmonitor_applied_v1";
  const STORE_DISCARDED = "jobmonitor_discarded_v1";

  function getState(key) {{
    try {{ return JSON.parse(localStorage.getItem(key) || "{{}}"); }}
    catch (e) {{ return {{}}; }}
  }}
  function saveState(key, obj) {{
    localStorage.setItem(key, JSON.stringify(obj));
  }}

  // ==================== Toggle actions ====================
  function toggleApplied(jobId) {{
    const applied = getState(STORE_APPLIED);
    const discarded = getState(STORE_DISCARDED);
    // If discarded, remove that first (mutually exclusive)
    if (discarded[jobId]) {{
      delete discarded[jobId];
      saveState(STORE_DISCARDED, discarded);
    }}
    if (applied[jobId]) {{
      delete applied[jobId];
    }} else {{
      applied[jobId] = {{ at: new Date().toISOString() }};
    }}
    saveState(STORE_APPLIED, applied);
    render();
  }}

  function toggleDiscarded(jobId) {{
    const applied = getState(STORE_APPLIED);
    const discarded = getState(STORE_DISCARDED);
    // If applied, remove that first (mutually exclusive)
    if (applied[jobId]) {{
      delete applied[jobId];
      saveState(STORE_APPLIED, applied);
    }}
    if (discarded[jobId]) {{
      delete discarded[jobId];
    }} else {{
      discarded[jobId] = {{ at: new Date().toISOString() }};
    }}
    saveState(STORE_DISCARDED, discarded);
    render();
  }}

  function markPending(jobId) {{
    // Auto-suggest applying after 8s (only if not already applied/discarded)
    setTimeout(() => {{
      const applied = getState(STORE_APPLIED);
      const discarded = getState(STORE_DISCARDED);
      if (!applied[jobId] && !discarded[jobId] &&
          confirm("Did you apply for this job? Click OK to mark as Applied.")) {{
        toggleApplied(jobId);
      }}
    }}, 8000);
  }}

  function resetState(which) {{
    const label = which === "applied" ? "APPLIED" : "DISCARDED";
    if (!confirm(`Reset ALL ${{label}} jobs? This cannot be undone.`)) return;
    localStorage.removeItem(which === "applied" ? STORE_APPLIED : STORE_DISCARDED);
    render();
  }}

  function toggleSection(listId, headerEl) {{
    const el = document.getElementById(listId);
    const icon = headerEl.querySelector(".toggle-icon");
    el.classList.toggle("collapsed");
    if (icon) icon.textContent = el.classList.contains("collapsed") ? "▶" : "▼";
  }}

  // ==================== Render ====================
  function render() {{
    const applied = getState(STORE_APPLIED);
    const discarded = getState(STORE_DISCARDED);

    const appliedCount = Object.keys(applied).length;
    const discardedCount = Object.keys(discarded).length;

    document.getElementById("applied-count").textContent = appliedCount;
    document.getElementById("applied-badge").textContent = appliedCount;
    document.getElementById("discarded-count").textContent = discardedCount;
    document.getElementById("discarded-badge").textContent = discardedCount;

    const appliedList    = document.getElementById("applied-list");
    const discardedList  = document.getElementById("discarded-list");
    const appliedSection = document.getElementById("applied-section");
    const discardedSection = document.getElementById("discarded-section");
    const highList = document.getElementById("high-list");
    const medList  = document.getElementById("med-list");

    document.querySelectorAll(".job-card").forEach(card => {{
      const jid = card.getAttribute("data-job-id");
      const btnApplied  = document.getElementById("btn-applied-" + jid);
      const btnDiscard  = document.getElementById("btn-discard-" + jid);

      // Remember origin (first render)
      if (!card.getAttribute("data-origin")) {{
        if (card.parentElement === highList) card.setAttribute("data-origin","high");
        else if (card.parentElement === medList) card.setAttribute("data-origin","med");
      }}

      // Clear all state classes
      card.classList.remove("applied","discarded");
      if (btnApplied) {{
        btnApplied.classList.remove("done");
        btnApplied.textContent = "✓ Mark as Applied";
      }}
      if (btnDiscard) {{
        btnDiscard.classList.remove("done");
        btnDiscard.textContent = "✕ Not a fit";
      }}

      if (applied[jid]) {{
        card.classList.add("applied");
        if (btnApplied) {{
          btnApplied.classList.add("done");
          btnApplied.textContent = "Undo Applied";
        }}
        appliedList.appendChild(card);
      }} else if (discarded[jid]) {{
        card.classList.add("discarded");
        if (btnDiscard) {{
          btnDiscard.classList.add("done");
          btnDiscard.textContent = "Undo Discard";
        }}
        discardedList.appendChild(card);
      }} else {{
        // Back to origin section
        const target = card.getAttribute("data-origin") === "med" ? medList : highList;
        target.appendChild(card);
      }}
    }});

    appliedSection.style.display = appliedCount > 0 ? "block" : "none";
    discardedSection.style.display = discardedCount > 0 ? "block" : "none";
  }}

  // Initial
  document.addEventListener("DOMContentLoaded", render);
</script>

</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def send_daily_digest():
    """Query today's matches, build HTML report, send single desktop toast."""
    matches = get_todays_matches()
    today = date.today().isoformat()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"daily_{today}.html")
    build_html_report(matches, report_path)

    n = len(matches)
    high = sum(1 for m in matches if m["score"] >= SCORE_THRESHOLD_HIGH)

    if n == 0 and DIGEST_SILENT_IF_EMPTY:
        log.info("Daily digest: 0 matches. Silent mode - no popup shown.")
        return report_path, 0

    if n == 0:
        title = "📋 Job Monitor · No new matches today"
        msg   = "Report: 0 matches. Click to open (empty report)."
    else:
        title = f"📋 Job Monitor · {n} new matches today"
        msg   = f"{high} HIGH · {n-high} MEDIUM · Click to open full report"

    file_url = "file:///" + report_path.replace("\\", "/")
    send_toast(title=title, message=msg, url=file_url, tag=f"digest-{today}")
    log.info("Daily digest sent. %d matches, report: %s", n, report_path)
    return report_path, n


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path, n = send_daily_digest()
    print(f"Digest generated. {n} matches. Report: {path}")
