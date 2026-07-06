import os
import urllib.parse
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

URL = "https://careers.swiggy.com/#/careers?career_page_category=Technology"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)

        page.wait_for_selector("iframe", timeout=30000)
        frame = page.frame_locator("iframe").first
        frame.locator("table tbody tr").first.wait_for(timeout=30000)

        rows = frame.locator("table tbody tr").all()
        jobs = []
        for r in rows:
            cells = r.locator("td").all_inner_texts()
            if len(cells) >= 4:
                jobs.append({
                    "id": cells[0].strip(),
                    "title": cells[1].strip(),
                    "location": cells[2].strip(),
                    "unit": cells[3].strip(),
                })
        browser.close()
        return jobs

def format_msg(jobs):
    import datetime
    today = datetime.date.today().isoformat()
    if not jobs:
        return f"Swiggy Technology jobs — {today}\nNo tech roles found."
    lines = [f"Swiggy Technology jobs — {today} ({len(jobs)} roles)"]
    for j in jobs:
        lines.append(f"- {j['title']} | {j['location']} | {j['unit']}")
    return "\n".join(lines)

def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram send failed: {e.code} {e.reason}; body={body}")

if __name__ == "__main__":
    jobs = scrape()
    msg = format_msg(jobs)
    send_telegram(msg)
    print(msg)
