import os
import requests
from playwright.sync_api import sync_playwright

THEATRE_URL = "https://in.bookmyshow.com/cinemas/CHEN/pvr-palazzo-the-nexus-vijaya-mall/buytickets/PVPZ/20261221"
TARGET_DATE = "20261221"
MOVIE_NAME = "avengers"
NTFY_TOPIC = os.environ["NTFY_TOPIC"]


def send_alert(message: str):
    resp = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": "BMS Tickets LIVE!", "Priority": "urgent"},
        timeout=15,
    )
    print(f"ntfy alert status: {resp.status_code}")


def check_tickets() -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        try:
            page.goto(THEATRE_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            if TARGET_DATE not in page.url:
                return False

            body_text = page.inner_text("body").lower()
            date_is_live = "21\ndec" in body_text or "21 dec" in body_text
            movie_is_live = MOVIE_NAME.lower() in body_text
            return date_is_live and movie_is_live
        finally:
            browser.close()


if __name__ == "__main__":
    send_alert("Test ping from GitHub!")
    if check_tickets():
        msg = f"🎟️ Tickets are LIVE for Avengers: Doomsday on Dec 21!\nBook now: {THEATRE_URL}"
        print(msg)
        send_alert(msg)
    else:
        print("Not open yet.")
