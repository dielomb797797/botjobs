# Probe 2 - hunt API endpoints & JSON blobs in Mollie page
import requests, re

r = requests.get(
    "https://jobs.mollie.com/",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    timeout=15,
)
html = r.text
print("size:", len(html))

# 1. All URLs that look like API calls
patterns = [
    r"https?://[^\"'\s<>]*api[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*teamtailor[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*greenhouse[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*lever[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*ashby[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*workable[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*recruitee[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*bamboohr[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*smartrecruiters[^\"'\s<>]*",
    r"https?://[^\"'\s<>]*/jobs\?[^\"'\s<>]*",
]
for p in patterns:
    hits = set(re.findall(p, html, re.IGNORECASE))
    if hits:
        print(f"\n=== pattern: {p}")
        for h in list(hits)[:8]:
            print(" -", h)

# 2. All hrefs containing 'job'
hrefs = re.findall(r'href="([^"]*job[^"]*)"', html, re.IGNORECASE)
uniq = sorted(set(hrefs))
print(f"\nhrefs containing 'job': {len(uniq)}")
for h in uniq[:15]:
    print(" -", h)

# 3. Structural HTML around "Sales Engineer" (proof they are in HTML)
idx = html.lower().find("sales engineer")
if idx >= 0:
    print(f"\nHTML around 'Sales Engineer' (idx={idx}):")
    print(html[max(0,idx-300):idx+400])
