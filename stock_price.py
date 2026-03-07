"""Fetch live stock prices and USD/INR exchange rate using yfinance."""
import yfinance as yf
from datetime import date


def _get_yf_ticker(ticker, market, exchange=""):
    """Convert ticker to yfinance format."""
    if market == "US":
        return ticker.upper()
    # Indian stocks: append .NS (NSE) or .BO (BSE)
    suffix = ".BO" if exchange.upper() == "BSE" else ".NS"
    return f"{ticker.upper()}{suffix}"


def fetch_stock_price(ticker, market="India", exchange=""):
    """Fetch current market price for a single stock."""
    try:
        yf_ticker = _get_yf_ticker(ticker, market, exchange)
        stock = yf.Ticker(yf_ticker)
        info = stock.fast_info
        price = getattr(info, "last_price", None)
        if price is None:
            price = getattr(info, "previous_close", None)
        if price:
            return {
                "ticker": ticker.upper(),
                "price": round(float(price), 2),
                "currency": "USD" if market == "US" else "INR",
            }
    except Exception:
        pass
    return None


def fetch_stock_prices_batch(holdings):
    """Fetch prices for multiple holdings. Returns dict of ticker -> price."""
    prices = {}
    tickers_map = {}

    for h in holdings:
        yf_t = _get_yf_ticker(h["ticker"], h["market"], h.get("exchange", ""))
        tickers_map[yf_t] = h["ticker"].upper()

    if not tickers_map:
        return prices

    try:
        yf_tickers = yf.Tickers(" ".join(tickers_map.keys()))
        for yf_t, orig_t in tickers_map.items():
            try:
                info = yf_tickers.tickers[yf_t].fast_info
                price = getattr(info, "last_price", None)
                if price is None:
                    price = getattr(info, "previous_close", None)
                if price:
                    prices[orig_t] = round(float(price), 2)
            except Exception:
                continue
    except Exception:
        # Fallback: fetch one by one
        for h in holdings:
            result = fetch_stock_price(h["ticker"], h["market"], h.get("exchange", ""))
            if result:
                prices[result["ticker"]] = result["price"]

    return prices


def fetch_usd_inr_rate():
    """Fetch current USD to INR exchange rate."""
    try:
        ticker = yf.Ticker("USDINR=X")
        info = ticker.fast_info
        rate = getattr(info, "last_price", None)
        if rate is None:
            rate = getattr(info, "previous_close", None)
        if rate:
            return {
                "rate": round(float(rate), 2),
                "date": date.today().isoformat(),
            }
    except Exception:
        pass
    return None
