# -*- coding: utf-8 -*-
"""
MATCHER - Scoring engine.
Takes a raw job posting (title, location, description) and returns a score 0-100
plus the list of matched keywords, applying hard exclusion filters.
"""
from config import (
    TARGET_LOCATIONS, TARGET_TITLES, CORE_DUTIES_KEYWORDS,
    SKILL_KEYWORDS, SENIORITY_ACCEPTED, EXCLUSION_KEYWORDS,
    TITLE_PREFIX_EXCLUSIONS,
)

# Weights (must sum to 100)
W_TITLE     = 40
W_LOCATION  = 20
W_SENIORITY = 15
W_DUTIES    = 15
W_SKILLS    = 10


def _norm(text: str) -> str:
    return (text or "").lower().strip()


def _contains_any(text: str, keywords) -> list:
    """Return list of keywords found in text."""
    return [kw for kw in keywords if kw in text]


def score_job(title: str, location: str, description: str = "") -> dict:
    """
    Score a job posting.
    Returns dict:
        {
          'score': int 0-100,
          'matched': {'title':[], 'location':[], 'duties':[], 'skills':[], 'seniority':[]},
          'excluded_by': [list of exclusion kw hit] (empty if ok),
          'passes_hard_filters': bool
        }
    """
    title_l = _norm(title)
    loc_l   = _norm(location)
    desc_l  = _norm(description)
    full_l  = f"{title_l} {loc_l} {desc_l}"

    # --- TITLE-PREFIX EXCLUSION (Senior/Staff/Principal/Lead/Director etc.) ---
    for prefix in TITLE_PREFIX_EXCLUSIONS:
        if title_l.startswith(prefix):
            return {
                "score": 0,
                "matched": {},
                "excluded_by": [f"title_starts_with:{prefix.strip()}"],
                "passes_hard_filters": False,
                "reason": "seniority_too_high",
            }

    # --- KEYWORD EXCLUSION CHECK (kill switch) ---
    excluded_by = _contains_any(full_l, EXCLUSION_KEYWORDS)
    if excluded_by:
        return {
            "score": 0,
            "matched": {},
            "excluded_by": excluded_by,
            "passes_hard_filters": False,
        }

    # --- LOCATION HARD FILTER ---
    loc_matches = _contains_any(loc_l or full_l, TARGET_LOCATIONS)
    if not loc_matches:
        # location is a HARD filter - no location match => reject
        return {
            "score": 0,
            "matched": {"location": []},
            "excluded_by": [],
            "passes_hard_filters": False,
            "reason": "location_not_in_target",
        }

    # --- SCORING ---
    title_matches     = _contains_any(title_l, TARGET_TITLES)
    duties_matches    = _contains_any(desc_l, CORE_DUTIES_KEYWORDS)
    skills_matches    = _contains_any(desc_l, SKILL_KEYWORDS)
    seniority_matches = _contains_any(full_l, SENIORITY_ACCEPTED)

    # Title: full weight if any exact match
    s_title = W_TITLE if title_matches else 0

    # Location: full weight if match (already validated above)
    s_location = W_LOCATION

    # Seniority: full if match; if not detectable, give half (many posts omit it)
    s_seniority = W_SENIORITY if seniority_matches else int(W_SENIORITY * 0.5)

    # Duties: scale by how many matched (cap at 5)
    s_duties = int(W_DUTIES * min(len(duties_matches), 5) / 5)

    # Skills: same logic (cap at 4)
    s_skills = int(W_SKILLS * min(len(skills_matches), 4) / 4)

    total = s_title + s_location + s_seniority + s_duties + s_skills

    return {
        "score": total,
        "matched": {
            "title":     title_matches,
            "location":  loc_matches,
            "seniority": seniority_matches,
            "duties":    duties_matches,
            "skills":    skills_matches,
        },
        "breakdown": {
            "title":     s_title,
            "location":  s_location,
            "seniority": s_seniority,
            "duties":    s_duties,
            "skills":    s_skills,
        },
        "excluded_by": [],
        "passes_hard_filters": True,
    }


def flatten_matched(matched: dict) -> str:
    """For DB logging / notifications."""
    parts = []
    for cat, kws in matched.items():
        if kws:
            parts.append(f"{cat}=[{', '.join(kws)}]")
    return " | ".join(parts)


# --- Self-test ---
if __name__ == "__main__":
    tests = [
        ("Solutions Engineer", "Amsterdam, Netherlands",
         "Onboarding B2B clients via REST API. Python, JSON, Postman. Entry level."),
        ("Account Executive", "Madrid",
         "Outbound prospecting, cold calling, quota-carrying."),
        ("Integration Specialist", "London",
         "REST API integration."),
        ("Technical Account Manager", "Madrid",
         "Root cause analysis, API troubleshooting, LLM tooling. Associate level."),
    ]
    for t, l, d in tests:
        r = score_job(t, l, d)
        print(f"\n[{t} @ {l}]  score={r['score']}  pass={r['passes_hard_filters']}")
        if r.get("excluded_by"): print("  excluded_by:", r["excluded_by"])
        if r.get("reason"):      print("  reason:", r["reason"])
        if r.get("breakdown"):   print("  breakdown:", r["breakdown"])
