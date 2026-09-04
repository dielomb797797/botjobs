# -*- coding: utf-8 -*-
"""
BASE SCRAPER - Common HTTP + parsing utilities.
Each site-specific scraper (mollie.py, booking.py, ...) exposes:
    fetch_jobs() -> list[dict]  with keys: title, location, url, description
"""
import logging
import requests
from bs4 import BeautifulSoup

from config import HTTP_TIMEOUT, USER_AGENT

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def http_get(url: str, extra_headers: dict | None = None) -> str | None:
    """GET request returning text, or None on failure."""
    try:
        h = dict(HEADERS)
        if extra_headers:
            h.update(extra_headers)
        r = requests.get(url, headers=h, timeout=HTTP_TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log.warning("http_get failed for %s : %s", url, e)
        return None


def http_get_json(url: str, extra_headers: dict | None = None):
    """GET request returning parsed JSON, or None on failure."""
    try:
        h = dict(HEADERS)
        h["Accept"] = "application/json"
        if extra_headers:
            h.update(extra_headers)
        r = requests.get(url, headers=h, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("http_get_json failed for %s : %s", url, e)
        return None


def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class ScraperResult(dict):
    """Standard dict shape for one job: title, location, url, description."""
    pass
