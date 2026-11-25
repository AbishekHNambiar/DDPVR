import os
import re
import requests
from playwright.sync_api import sync_playwright

BMS_URL = "https://in.bookmyshow.com/cinemas/CHEN/pvr-palazzo-the-nexus-vijaya-mall/buytickets/PVPZ/20261221"
PVR_URL = "https://www.pvrcinemas.com/cinemasessions/Chennai/PVR-Palazzo-The-Nexus-Vijaya-Mall/388"
TARGET_DATE = "20261221"
MOVIE_NAME = "avengers"
NTFY_TOPIC = os.environ["NTFY_TOPIC"]


def send_alert(title: str, message: str):
    resp = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "urgent"},
        timeout=15,
    )
    print(f"ntfy alert status: {resp.status_code}")


def check_bms(context) -> bool:
    page = context.new_page()
    try:
        page.goto(BMS_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(4000)

        if TARGET_DATE not in page.url:
            return False

        body_text = page.inner_text("body").lower()
        date_is_live = "21\ndec" in body_text or "21 dec" in body_text
        movie_is_live = MOVIE_NAME in body_text
        return date_is_live and movie_is_live
    except Exception as e:
        print(f"BMS check error: {e}")
        return False
    finally:
        page.close()


def check_pvr(context) -> bool:
    page = context.new_page()
    try:
        page.goto(PVR_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        body_text = page.inner_text("body").lower()
        # Look for "21 Mon" (Dec 21, 2026 is a Monday) in the date bar
        if not re.search(r"\b21\s+mon\b|\bmon\s+21\b", body_text):
            return False

        # Click the Dec 21 tab to confirm Avengers is listed for that day
        dec21_tab = page.locator("div, button, li, a").filter(has_text=re.compile(r"^\s*(dec\s*)?21\s*mon\s*$", re.I)).first
        if dec21_tab.count() > 0:
            dec21_tab.click()
            page.wait_for_timeout(3000)
            body_text = page.inner_text("body").lower()

        return MOVIE_NAME in body_text
    except Exception as e:
        print(f"PVR check error: {e}")
        return False
    finally:
        page.close()


if __name__ == "__main__":
    send_alert("Test ping from GitHub!")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            )
        )
        try:
            bms_live = check_bms(context)
            pvr_live = check_pvr(context)
        finally:
            browser.close()

    if bms_live:
        msg = f"🎟️ BMS Tickets LIVE for Avengers: Doomsday (Dec 21)!\n{BMS_URL}"
        print(msg)
        send_alert("BMS Tickets LIVE!", msg)
    else:
        print("BMS: Not open yet.")

    if pvr_live:
        msg = f"🎟️ PVR Tickets LIVE for Avengers: Doomsday (Dec 21)!\n{PVR_URL}"
        print(msg)
        send_alert("PVR Tickets LIVE!", msg)
    else:
        print("PVR: Not open yet.")
