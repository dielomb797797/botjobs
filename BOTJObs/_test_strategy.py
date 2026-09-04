# -*- coding: utf-8 -*-
"""Verifica: i ruoli 'Strategy & Operations' passano il matcher?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matcher import score_job

tests = [
    # Titolo tipico Strategy & Ops
    ("Strategy and Operations Manager",
     "Amsterdam",
     "Drive strategic initiatives, cross-functional stakeholder management, "
     "operations excellence, KPIs, business analysis."),

    # Graduate program (che avevi visto ieri nel DB)
    ("Graduate Programme 2027: Strategy & Operations Manager",
     "Madrid",
     "Rotational graduate program covering strategy, operations, analytics. "
     "Entry-level associate track."),

    # Business Ops Manager
    ("Business Operations Manager",
     "Amsterdam",
     "Process optimization, automation, workflow, scale operations, cross-functional."),

    # Product Operations (che invece E' nel tuo target)
    ("Product Operations Manager",
     "Amsterdam",
     "Product ops, workflow, automation, api, cross-functional teams."),

    # Strategy & Ops ma con TANTA componente tecnica in descrizione
    ("Strategy and Operations Analyst",
     "Amsterdam",
     "API integrations, workflow automation, python, sql, postman, "
     "REST API troubleshooting, technical stakeholder alignment, LLM tooling."),

    # Pure Strategy (senza Operations)
    ("Strategy Manager - Payments",
     "Amsterdam",
     "Strategic planning, market analysis, competitive intelligence."),
]

print(f"{'SCORE':<7}{'PASS':<7}{'REASON':<25}TITLE")
print("=" * 100)
for title, loc, desc in tests:
    r = score_job(title, loc, desc)
    score = r["score"]
    ok = "YES" if r["passes_hard_filters"] else "NO"
    reason = ""
    if r.get("reason"):
        reason = r["reason"]
    elif r.get("excluded_by"):
        reason = f"excl:{r['excluded_by'][0]}"
    matched_titles = r.get("matched", {}).get("title", []) if r["passes_hard_filters"] else []
    match_info = f" -> title match: {matched_titles}" if matched_titles else ""
    print(f"{score:<7}{ok:<7}{reason:<25}{title}{match_info}")
    if r["passes_hard_filters"]:
        b = r.get("breakdown", {})
        print(f"       breakdown: title={b.get('title')} loc={b.get('location')} sen={b.get('seniority')} duties={b.get('duties')} skills={b.get('skills')}")
