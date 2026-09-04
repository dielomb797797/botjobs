# -*- coding: utf-8 -*-
"""
Test Playwright on the 6 remaining companies.
Strategy: open page, wait for content to load, intercept network calls
to find the real API endpoint OR extract from rendered DOM.
"""
import asyncio, time
from playwright.async_api import async_playwright

SITES = [
    ("Revolut",   "https://www.revolut.com/careers/", "Amsterdam OR Madrid"),
    ("Backbase",  "https://www.backbase.com/careers/jobs", "Amsterdam"),
    ("Atlassian", "https://www.atlassian.com/company/careers/all-jobs?team=&location=Netherlands", "Netherlands"),
    ("Justeat",   "https://careers.justeattakeaway.com/global/en/search-results?keywords=engineer", "Amsterdam"),
    ("Booking",   "https://jobs.booking.com/booking/jobs?in_iframe=1", "Amsterdam"),
    ("Cisco",     "https://jobs.cisco.com/jobs/SearchJobs/?21178=%5B37704%5D&21178_format=6020", "Madrid"),
]


async def probe(pw, name, url, note):
    """Open page, capture XHR/fetch API calls, extract job count from DOM."""
    print(f"\n{'='*70}\n{name}: {url[:80]}\n{'='*70}")
    api_calls = []
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1400, "height": 900},
    )
    page = await context.new_page()

    # Capture network requests
    def on_response(response):
        try:
            u = response.url
            ct = response.headers.get("content-type","")
            if ("json" in ct or "graphql" in u.lower()) and response.status == 200:
                # relevant filter
                if any(kw in u.lower() for kw in
                       ["job","career","position","search","apply","opening","vacancy"]):
                    api_calls.append({"url": u, "status": response.status,
                                      "size": int(response.headers.get("content-length","0") or 0)})
        except Exception:
            pass

    page.on("response", on_response)

    t0 = time.time()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # give the SPA time to load jobs via XHR
        await page.wait_for_timeout(4000)
        # try scrolling to trigger lazy loads
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"  ERROR loading: {e}")

    elapsed = round(time.time()-t0, 1)

    # Extract job count from DOM
    dom_stats = await page.evaluate("""() => {
        const t = document.body.innerText || "";
        // Count elements that look like job cards
        const links = Array.from(document.querySelectorAll('a')).filter(a => {
            const href = (a.href||"").toLowerCase();
            const text = (a.innerText||"").trim();
            return (href.includes('/job') || href.includes('/position') ||
                    href.includes('/careers/') || href.includes('/apply/') ||
                    href.includes('greenhouse') || href.includes('lever') ||
                    href.includes('workday')) && text.length > 3 && text.length < 200;
        });
        // Count "engineer" / "manager" / "specialist" mentions
        const engCnt = (t.match(/engineer/gi)||[]).length;
        const mgrCnt = (t.match(/manager/gi)||[]).length;
        return {
            pageLen: t.length,
            jobLinks: links.length,
            firstLinks: links.slice(0,5).map(a => ({
                text: (a.innerText||"").trim().substring(0,80),
                href: (a.href||"").substring(0,120),
            })),
            engineerHits: engCnt,
            managerHits: mgrCnt,
        };
    }""")

    print(f"  Load time: {elapsed}s | Page text: {dom_stats['pageLen']} chars")
    print(f"  Job-like links found in DOM: {dom_stats['jobLinks']}")
    print(f"  Keyword hits: 'engineer'={dom_stats['engineerHits']}, "
          f"'manager'={dom_stats['managerHits']}")
    print(f"  API calls intercepted: {len(api_calls)}")
    for c in api_calls[:5]:
        print(f"     - {c['url'][:110]}")
    print(f"  Sample DOM links:")
    for l in dom_stats["firstLinks"][:5]:
        print(f"     - {l['text']!r}")
        print(f"       {l['href']}")

    await browser.close()
    return {
        "company": name,
        "elapsed": elapsed,
        "job_links": dom_stats["jobLinks"],
        "api_calls": api_calls,
    }


async def main():
    async with async_playwright() as pw:
        # Sequential for cleaner output (parallel would be faster)
        results = []
        overall_start = time.time()
        for name, url, note in SITES:
            r = await probe(pw, name, url, note)
            results.append(r)
        total = round(time.time() - overall_start, 1)

    print("\n" + "="*70)
    print(f"SUMMARY (total: {total}s)")
    print("="*70)
    print(f"{'COMPANY':<12}{'TIME':<8}{'DOM LINKS':<12}{'API CALLS':<12}STATUS")
    for r in results:
        status = "OK" if r["job_links"] > 3 or r["api_calls"] else "??"
        print(f"{r['company']:<12}{r['elapsed']}s{'':<4}{r['job_links']:<12}{len(r['api_calls']):<12}{status}")


asyncio.run(main())
