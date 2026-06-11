import json
import os
import smtplib
import urllib.request
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CONFIG = json.loads(Path("config.json").read_text())
SEEN_FILE = Path("seen.json")
MAX_PRICE = CONFIG["max_price"]
EMAIL_TO = CONFIG["email_to"]
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_PASS = os.environ.get("GMAIL_PASS", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Shared Playwright browser instance (set in main)
_browser = None


def get(url):
    r = SESSION.get(url, timeout=15)
    r.raise_for_status()
    return r.text


def get_js(url, wait_for=None, timeout=20000):
    page = _browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        if wait_for:
            try:
                page.wait_for_selector(wait_for, timeout=10000)
            except Exception:
                pass
        else:
            page.wait_for_timeout(3000)
        return page.content()
    finally:
        page.close()


def soup(html):
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Scrapers – requests (statiniai puslapiai)
# ---------------------------------------------------------------------------

def scrape_maasland():
    html = get("https://maaslandrelocation.nl/en/properties?type=rent&city=maastricht")
    s = soup(html)
    results = []
    for card in s.select(".property-item, .listing-item, article"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://maaslandrelocation.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"maasland-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_vbt():
    html = get("https://vbtverhuurmakelaars.nl/huurwoningen-maastricht")
    s = soup(html)
    results = []
    for card in s.select(".property-card, .woning, .listing, article, .object"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://vbtverhuurmakelaars.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"vbt-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_housing4you():
    html = get("https://www.housing4you.eu/huurders")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .object"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.housing4you.eu" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"h4y-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_househunting():
    html = get("https://househunting.nl/en/vestigingen/househunting-maastricht/")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .woning"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://househunting.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"hh-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_hypodomus():
    html = get("https://www.hypodomus-maastricht.nl/aanbod/woningaanbod/huur/")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .object"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.hypodomus-maastricht.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"hypo-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_huizenbeheer():
    html = get("https://huizenbeheermaastricht.nl/verhuur/")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .woning, .post"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://huizenbeheermaastricht.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"hbm-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_kamermaastricht():
    html = get("https://www.kamermaastricht.com/")
    s = soup(html)
    results = []
    for card in s.select(".listing, .property, article, .kamer"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.kamermaastricht.com" + href
        if "?" in href and "action_" in href:
            continue
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"km-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_prohousing():
    html = get("https://www.pro-housingrooms.nl/nl/")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .room"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.pro-housingrooms.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"ph-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_roofz():
    html = get("https://roofz.eu/huur/woningen")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .apartment-card, .home-card"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://roofz.eu" + href
        title = card.get_text(" ", strip=True)[:120]
        if "maastricht" not in title.lower():
            continue
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"roofz-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_woonplein():
    html = get("https://woonpleinlimburg.nl/en/zoek-woningen/huur/nederland/maastricht/appartement")
    s = soup(html)
    results = []
    for card in s.select(".property, .listing, article, .woning-item"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://woonpleinlimburg.nl" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"wp-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


# ---------------------------------------------------------------------------
# Scrapers – Playwright (JavaScript-rendered puslapiai)
# ---------------------------------------------------------------------------

def scrape_pararius():
    html = get_js(
        "https://www.pararius.com/apartments/maastricht/0-750",
        wait_for=".listing-search-item",
    )
    s = soup(html)
    results = []
    for card in s.select(".listing-search-item"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.pararius.com" + href
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"par-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_funda():
    html = get_js(
        "https://www.funda.nl/zoeken/huur/?selected_area=%5B%22maastricht%22%5D&price=%22-750%22",
        wait_for="[data-test-id='search-result-item']",
    )
    s = soup(html)
    results = []
    for card in s.select("[data-test-id='search-result-item'], .search-result__header-title-col"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.funda.nl" + href
        if "/detail/" not in href and "/huur/" not in href:
            continue
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"funda-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_kamernet():
    html = get_js(
        "https://kamernet.nl/en/for-rent/rooms-maastricht",
        wait_for="a[href*='/for-rent/']",
    )
    s = soup(html)
    results = []
    seen_hrefs = set()
    for a in s.find_all("a", href=True):
        href = a["href"]
        if "/for-rent/" not in href or "maastricht" not in href.lower():
            continue
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        if not href.startswith("http"):
            href = "https://kamernet.nl" + href
        title = a.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"kn-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_huure():
    html = get_js(
        "https://huure.nl/rental-property/maastricht",
        wait_for=".property-card",
    )
    s = soup(html)
    results = []
    for card in s.select(".property-card, [class*='property-card']"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://huure.nl" + href
        if "/huurwoningen/" not in href:
            continue
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"huure-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_housinganywhere():
    html = get_js(
        "https://housinganywhere.com/s/Maastricht--Netherlands/student-accommodation?maxPrice=750",
        wait_for="a[href*='/Maastricht/']",
        timeout=30000,
    )
    s = soup(html)
    results = []
    seen_hrefs = set()
    for a in s.find_all("a", href=True):
        href = a["href"]
        if "Maastricht" not in href:
            continue
        if not any(x in href for x in ["/room/", "/apartment/", "/studio/"]):
            continue
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        if not href.startswith("http"):
            href = "https://housinganywhere.com" + href
        title = a.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"ha-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_price(text):
    import re
    match = re.search(r"[€]?\s*(\d[\d\.,]+)\s*(p/?m|per maand|/maand|pm|,-)?", text, re.IGNORECASE)
    if match:
        raw = match.group(1).replace(".", "").replace(",", "")
        try:
            val = int(raw)
            if 100 < val < 10000:
                return val
        except ValueError:
            pass
    return None


SCRAPERS = {
    "pararius": scrape_pararius,
    "funda": scrape_funda,
    "kamernet": scrape_kamernet,
    "huure": scrape_huure,
    "housinganywhere": scrape_housinganywhere,
    "kamermaastricht": scrape_kamermaastricht,
    "maasland": scrape_maasland,
    "vbt": scrape_vbt,
    "housing4you": scrape_housing4you,
    "househunting": scrape_househunting,
    "hypodomus": scrape_hypodomus,
    "huizenbeheer": scrape_huizenbeheer,
    "prohousing": scrape_prohousing,
    "roofz": scrape_roofz,
    "woonpleinlimburg": scrape_woonplein,
}


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _discord_post(content):
    payload = json.dumps({"content": content}).encode()
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com/rental-monitor, 1.0)",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=10)


def send_discord(listings):
    if not DISCORD_WEBHOOK:
        return
    header = f"**Nauji Mastrichto nuomos skelbimai** ({len(listings)} vnt., ≤€{MAX_PRICE}/mėn.)\n"
    chunk = header
    for l in listings:
        line = f"• [{l['title'][:70]}]({l['url']}) — €{l['price']}/mėn.\n"
        if len(chunk) + len(line) > 1900:
            _discord_post(chunk)
            chunk = ""
        chunk += line
    if chunk.strip():
        _discord_post(chunk)
    print(f"Discord pranešimas išsiųstas ({len(listings)} skelbimai)")


def send_email(listings):
    if not GMAIL_PASS:
        return
    sender = GMAIL_USER or EMAIL_TO
    lines = [f"Rasta {len(listings)} naujų būstų Mastrichte (≤€{MAX_PRICE}/mėn.):\n"]
    for l in listings:
        lines.append(f"• {l['title'][:80]}\n  Kaina: €{l['price']}/mėn.\n  {l['url']}\n")
    msg = MIMEText("\n".join(lines), "plain", "utf-8")
    msg["Subject"] = f"[Maastricht Nuoma] {len(listings)} naujų skelbimų"
    msg["From"] = sender
    msg["To"] = EMAIL_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, GMAIL_PASS)
        s.sendmail(sender, EMAIL_TO, msg.as_string())
    print(f"El. laiškas išsiųstas į {EMAIL_TO}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()


def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(sorted(seen), indent=2))


def main():
    global _browser
    seen = load_seen()
    new_listings = []
    enabled = CONFIG.get("sites", list(SCRAPERS.keys()))

    js_sites = {"pararius", "funda", "kamernet", "huure", "housinganywhere"}
    needs_browser = any(s in js_sites for s in enabled)

    with sync_playwright() as pw:
        if needs_browser:
            _browser = pw.chromium.launch(headless=True)

        for name in enabled:
            scraper = SCRAPERS.get(name)
            if not scraper:
                continue
            try:
                items = scraper()
                new_count = 0
                for item in items:
                    if item["id"] not in seen:
                        new_listings.append(item)
                        seen.add(item["id"])
                        new_count += 1
                print(f"{name}: {len(items)} skelbimai, {new_count} nauji")
            except Exception as e:
                print(f"{name}: klaida – {e}")

        if _browser:
            _browser.close()

    save_seen(seen)

    if new_listings:
        print(f"\nRasta {len(new_listings)} naujų skelbimų – siunčiami pranešimai...")
        send_discord(new_listings)
        send_email(new_listings)
    else:
        print("Naujų skelbimų nerasta.")


if __name__ == "__main__":
    main()
