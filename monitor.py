import json
import os
import smtplib
import urllib.request
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup

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


def get(url):
    r = SESSION.get(url, timeout=15)
    r.raise_for_status()
    return r.text


def soup(html):
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Scrapers – each returns list of {"id": str, "title": str, "price": str, "url": str}
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
        uid = href.split("?")[0].rstrip("/").split("/")[-1]
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
        # skip filter/action links
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
    html = get(
        "https://woonpleinlimburg.nl/en/zoek-woningen/huur/nederland/maastricht/appartement"
    )
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


def scrape_pararius():
    r = SESSION.get(
        "https://www.pararius.com/apartments/maastricht/0-750",
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/",
        },
        timeout=15,
    )
    r.raise_for_status()
    s = soup(r.text)
    results = []
    for card in s.select(".listing-search-item"):
        link = card.find("a", class_="listing-search-item__link--title", href=True)
        if not link:
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
    url = (
        "https://www.funda.nl/zoeken/huur/"
        "?selected_area=%5B%22maastricht%22%5D"
        "&price=%22-750%22"
        "&object_type=%5B%22apartment%22%2C%22house%22%5D"
    )
    html = get(url)
    s = soup(html)
    results = []
    for card in s.select("[data-test-id='search-result-item'], .search-result, article"):
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
    html = get("https://kamernet.nl/en/for-rent/rooms-maastricht")
    s = soup(html)
    results = []
    for card in s.select(".tile, .listing-tile, [class*='tile'], [class*='listing']"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://kamernet.nl" + href
        if "/for-rent/" not in href:
            continue
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"kn-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_huure():
    html = get("https://huure.nl/rental-property/maastricht")
    s = soup(html)
    results = []
    for card in s.select(".property-card, .listing-card, article, [class*='property'], [class*='listing']"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://huure.nl" + href
        if "/huurwoningen/" not in href and "/rental-property/" not in href:
            continue
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"huure-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


def scrape_housinganywhere():
    html = get(
        "https://housinganywhere.com/s/Maastricht--Netherlands/student-accommodation"
        "?maxPrice=750"
    )
    s = soup(html)
    results = []
    for card in s.select("[class*='listing'], [class*='property'], article"):
        link = card.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            href = "https://housinganywhere.com" + href
        if "/rooms/" not in href and "/apartments/" not in href and "/studios/" not in href:
            continue
        title = card.get_text(" ", strip=True)[:120]
        price = extract_price(title)
        if price and price > MAX_PRICE:
            continue
        uid = href.rstrip("/").split("/")[-1]
        results.append({"id": f"ha-{uid}", "title": title, "price": str(price or "?"), "url": href})
    return results


SCRAPERS = {
    "pararius": scrape_pararius,
    "funda": scrape_funda,
    "kamernet": scrape_kamernet,
    "huure": scrape_huure,
    "housinganywhere": scrape_housinganywhere,
    "maasland": scrape_maasland,
    "vbt": scrape_vbt,
    "housing4you": scrape_housing4you,
    "househunting": scrape_househunting,
    "hypodomus": scrape_hypodomus,
    "huizenbeheer": scrape_huizenbeheer,
    "kamermaastricht": scrape_kamermaastricht,
    "prohousing": scrape_prohousing,
    "roofz": scrape_roofz,
    "woonpleinlimburg": scrape_woonplein,
}


# ---------------------------------------------------------------------------
# Notification
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
    sent = 0
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
    seen = load_seen()
    new_listings = []

    enabled = CONFIG.get("sites", list(SCRAPERS.keys()))
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

    save_seen(seen)

    if new_listings:
        print(f"\nRasta {len(new_listings)} naujų skelbimų – siunčiami pranešimai...")
        send_discord(new_listings)
        send_email(new_listings)
    else:
        print("Naujų skelbimų nerasta.")


if __name__ == "__main__":
    main()
