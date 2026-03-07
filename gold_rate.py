import requests
from bs4 import BeautifulSoup
from datetime import date


def _parse_rate(text):
    """Parse a rate value from text like '₹16,364' or '₹15,000(+230)'."""
    text = text.split("(")[0]  # remove trailing (+251) etc.
    text = text.replace("₹", "").replace(",", "").replace("Rs.", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def fetch_gold_rate_pune():
    """Fetch today's gold rate for Pune from GoodReturns."""
    try:
        url = "https://www.goodreturns.in/gold-rates/pune.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        rate_22k = None
        rate_24k = None

        tables = soup.find_all("table")

        # Table 0 = 24K rates, Table 1 = 22K rates
        # Each has rows: header, 1g, 8g, 10g, 100g
        # We want the 1g row (index 1), "Today" column (index 1)
        for i, table in enumerate(tables[:3]):
            rows = table.find_all("tr")
            if len(rows) >= 2:
                cells = rows[1].find_all("td")
                if len(cells) >= 2:
                    gram_label = cells[0].get_text(strip=True)
                    if gram_label == "1":
                        val = _parse_rate(cells[1].get_text(strip=True))
                        if val:
                            if i == 0:
                                rate_24k = val
                            elif i == 1:
                                rate_22k = val

        # Fallback: parse from the history table (Table 3)
        # Format: Date | 24K | 22K
        if rate_22k is None and len(tables) > 3:
            rows = tables[3].find_all("tr")
            if len(rows) >= 2:
                cells = rows[1].find_all("td")
                if len(cells) >= 3:
                    rate_24k = _parse_rate(cells[1].get_text(strip=True))
                    rate_22k = _parse_rate(cells[2].get_text(strip=True))

        if rate_22k:
            return {
                "rate_22k": round(rate_22k, 2),
                "rate_24k": round(rate_24k, 2) if rate_24k else None,
                "date": date.today().isoformat(),
                "source": "GoodReturns.in",
            }
    except Exception:
        pass

    # Fallback source
    try:
        url = "https://www.bankbazaar.com/gold-rate-pune.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        rate_22k = None
        rate_24k = None
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value_text = cells[-1].get_text(strip=True)
                    value_text = value_text.replace("Rs.", "").replace(",", "").replace("₹", "").strip()
                    try:
                        value = float(value_text)
                    except ValueError:
                        continue
                    if "22" in label:
                        rate_22k = value if value < 50000 else value / 10
                    elif "24" in label:
                        rate_24k = value if value < 50000 else value / 10

        if rate_22k:
            return {
                "rate_22k": round(rate_22k, 2),
                "rate_24k": round(rate_24k, 2) if rate_24k else None,
                "date": date.today().isoformat(),
                "source": "BankBazaar.com",
            }
    except Exception:
        pass

    return None
