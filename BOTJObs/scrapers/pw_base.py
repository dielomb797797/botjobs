# -*- coding: utf-8 -*-
"""
Playwright generic scraper - for sites that block simple HTTP or require JS.
Strategy modes:
  1. 'dom_links'      -> render page, collect <a> tags matching a URL pattern
  2. 'api_intercept'  -> render page, capture JSON XHR calls to a URL pattern
"""
import asyncio
import re
import logging
from playwright.async_api import async_playwright

log = logging.getLogger(__name__)

DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")


async def _dom_links_extract(url, url_pattern, wait_ms=4000, extra_wait_selector=None,
                             scroll_times=3, click_selector=None):
    """
    Open URL in headless Chromium, wait for JS, extract job links from DOM
    whose href matches url_pattern.
    Returns list of {title, location, url, description}.
    """
    jobs = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=DEFAULT_UA,
            viewport={"width": 1400, "height": 900},
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if extra_wait_selector:
                try:
                    await page.wait_for_selector(extra_wait_selector, timeout=15000)
                except Exception:
                    pass
            await page.wait_for_timeout(wait_ms)

            # Optional click to expand results
            if click_selector:
                try:
                    for _ in range(3):
                        btn = await page.query_selector(click_selector)
                        if not btn: break
                        await btn.click()
                        await page.wait_for_timeout(1500)
                except Exception:
                    pass

            # Scroll to trigger lazy loads
            for _ in range(scroll_times):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

            # Extract job cards - href matches pattern, get title + full text
            raw = await page.evaluate("""(pattern) => {
                const re = new RegExp(pattern, 'i');
                const links = Array.from(document.querySelectorAll('a'));
                const results = [];
                const seen = new Set();
                for (const a of links) {
                    const href = a.href || "";
                    if (!re.test(href)) continue;
                    if (seen.has(href)) continue;
                    seen.add(href);
                    // Try to get parent card text for location context
                    let parentText = "";
                    let el = a;
                    for (let i = 0; i < 4 && el; i++) {
                        el = el.parentElement;
                        if (el && el.innerText && el.innerText.length > 20 &&
                            el.innerText.length < 800) {
                            parentText = el.innerText;
                            break;
                        }
                    }
                    results.push({
                        title: (a.innerText || "").trim().substring(0, 300),
                        url: href,
                        context: parentText.substring(0, 500),
                    });
                }
                return results;
            }""", url_pattern)

            jobs = raw
        finally:
            await browser.close()
    return jobs


async def _api_intercept(url, api_pattern, wait_ms=6000):
    """
    Open URL, capture JSON responses whose URL matches api_pattern.
    Returns list of parsed JSON responses (raw).
    """
    captured = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=DEFAULT_UA)
        page = await context.new_page()

        async def on_response(response):
            try:
                u = response.url
                if re.search(api_pattern, u, re.IGNORECASE) and response.status == 200:
                    try:
                        data = await response.json()
                        captured.append({"url": u, "data": data})
                    except Exception:
                        pass
            except Exception:
                pass

        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(wait_ms)
            # Give more time for XHR
            for _ in range(2):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
        finally:
            await browser.close()
    return captured


def run_dom_extraction(url, url_pattern, **kwargs):
    """Sync wrapper for _dom_links_extract."""
    return asyncio.run(_dom_links_extract(url, url_pattern, **kwargs))


def run_api_intercept(url, api_pattern, **kwargs):
    """Sync wrapper for _api_intercept."""
    return asyncio.run(_api_intercept(url, api_pattern, **kwargs))


# ---- Helpers to parse job cards ----
def parse_card_text(text, title):
    """
    Extract location hint from card context text.
    E.g., 'Sales Engineer\nAmsterdam\nEngineering' -> 'Amsterdam'
    """
    if not text:
        return ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # Find line right after title
    for i, l in enumerate(lines):
        if l == title.strip() and i + 1 < len(lines):
            return lines[i + 1]
    # Fallback: look for known city names
    KNOWN = ["Amsterdam","Madrid","Barcelona","London","Berlin","Munich",
             "Rotterdam","Paris","Dublin","Netherlands","Spain","Remote"]
    for l in lines:
        for city in KNOWN:
            if city.lower() in l.lower():
                return l
    return ""
