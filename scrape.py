import os
from playwright.sync_api import sync_playwright
import requests

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
            if len(cells) < 4:
                continue
            title = cells[1].strip()
            location = cells[2].strip()
            unit = cells[3].strip()
            if not title or location in {"Location", ""} or unit in {"Unit", ""}:
                continue
            jobs.append({
                "id": cells[0].strip(),
                "title": title,
                "location": location,
                "unit": unit,
            })
        browser.close()
        return jobs

def format_msg(jobs):
    import datetime
    today = datetime.date.today().isoformat()
    if not jobs:
        return f"Swiggy Technology jobs — {today}\nNo tech roles found."
    lines = [
        f"Swiggy Technology jobs — {today}",
        f"Found {len(jobs)} open role{'s' if len(jobs) != 1 else ''}:",
        "",
    ]
    for idx, j in enumerate(jobs, 1):
        lines.append(f"{idx}. {j['title']}")
        lines.append(f"   Location: {j['location']}")
        lines.append(f"   Unit: {j['unit']}")
        lines.append("")
    return "\n".join(lines).rstrip()

def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }, timeout=20)
    resp.raise_for_status()

if __name__ == "__main__":
    jobs = scrape()
    msg = format_msg(jobs)
    send_telegram(msg)
    print(msg)
