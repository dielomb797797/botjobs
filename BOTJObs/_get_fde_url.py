import sqlite3, subprocess
conn = sqlite3.connect("data/jobs.db")
conn.row_factory = sqlite3.Row
row = conn.execute(
    "SELECT company, title, url, score, location FROM jobs "
    "WHERE company='Datasnipper' AND title LIKE '%Forward Deployed%'"
).fetchone()
if row:
    print(f"Found: {row['company']} - {row['title']}")
    print(f"Location: {row['location']}")
    print(f"Score: {row['score']}")
    print(f"URL: {row['url']}")
    # Open it in default browser
    subprocess.Popen(["cmd", "/c", "start", "", row['url']], shell=False)
    print("\nOpening in browser...")
else:
    print("Not found")
