"""Database layer — Supabase (PostgreSQL) backend.

Drop-in replacement for the SQLite version. All function signatures
are identical so app.py requires zero changes.
"""

import os
from datetime import date
from supabase import create_client, Client

# --- Supabase connection ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Allow local .streamlit/secrets.toml override
try:
    import streamlit as st
    if not SUPABASE_URL:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    if not SUPABASE_KEY:
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
except Exception:
    pass

_client: Client = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def _sb():
    """Shorthand for the Supabase client."""
    return _get_client()


class _DictRow(dict):
    """Dict subclass that also supports attribute-style and index-style access
    like sqlite3.Row so existing app code works unchanged."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def _row(data):
    """Convert a Supabase dict response to a _DictRow."""
    if data is None:
        return None
    return _DictRow(data)


def _rows(data_list):
    """Convert a list of dicts to _DictRow list."""
    if data_list is None:
        return []
    return [_DictRow(d) for d in data_list]


def init_db():
    """No-op for Supabase — tables are created via migrations."""
    pass


# ======================== SOURCES ========================

def add_source(name, category, liquidity, is_gold=False, gold_weight_grams=0):
    _sb().table("sources").insert({
        "name": name, "category": category, "liquidity": liquidity,
        "is_gold": bool(is_gold), "gold_weight_grams": gold_weight_grams,
    }).execute()


def get_sources(active_only=True):
    q = _sb().table("sources").select("*")
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("category").order("name").execute()
    return _rows(resp.data)


def update_source(source_id, name, category, liquidity, is_gold, gold_weight_grams):
    _sb().table("sources").update({
        "name": name, "category": category, "liquidity": liquidity,
        "is_gold": bool(is_gold), "gold_weight_grams": gold_weight_grams,
    }).eq("id", source_id).execute()


def deactivate_source(source_id):
    _sb().table("sources").update({"is_active": False}).eq("id", source_id).execute()


# ======================== BALANCES ========================

def get_latest_balance(source_id):
    resp = (_sb().table("balance_updates").select("balance")
            .eq("source_id", source_id)
            .order("update_date", desc=True).order("id", desc=True)
            .limit(1).execute())
    if resp.data:
        return resp.data[0]["balance"]
    return 0.0


def update_balance(source_id, new_balance, note="", update_date=None):
    prev = get_latest_balance(source_id)
    change = new_balance - prev
    if update_date is None:
        update_date = date.today().isoformat()
    _sb().table("balance_updates").insert({
        "source_id": source_id, "balance": new_balance,
        "previous_balance": prev, "change_amount": change,
        "note": note, "update_date": update_date,
    }).execute()


def get_balance_history(source_id=None, start_date=None, end_date=None):
    q = (_sb().rpc("get_balance_history_fn", {}) if False else
         _sb().table("balance_updates")
         .select("*, sources!inner(name, category, liquidity)")
         )
    # We'll do a simpler approach: join via select
    q = _sb().table("balance_updates").select(
        "id, source_id, balance, previous_balance, change_amount, note, updated_at, update_date, "
        "sources(name, category, liquidity)"
    )
    if source_id:
        q = q.eq("source_id", source_id)
    if start_date:
        q = q.gte("update_date", start_date)
    if end_date:
        q = q.lte("update_date", end_date)
    resp = q.order("update_date", desc=True).order("id", desc=True).execute()
    # Flatten the join
    result = []
    for r in resp.data or []:
        src = r.pop("sources", {}) or {}
        r["source_name"] = src.get("name", "")
        r["category"] = src.get("category", "")
        r["liquidity"] = src.get("liquidity", "")
        result.append(_DictRow(r))
    return result


def get_snapshot_on_date(target_date):
    """Get the latest balance for each active source as of target_date."""
    # Use RPC for complex query
    resp = _sb().rpc("get_snapshot_on_date", {"target_date": target_date}).execute()
    if resp.data:
        return _rows(resp.data)
    return []


def get_daily_totals(start_date=None, end_date=None):
    resp = _sb().rpc("get_daily_totals", {
        "p_start_date": start_date, "p_end_date": end_date,
    }).execute()
    if resp.data:
        return _rows(resp.data)
    return []


def get_source_daily_balances(source_id, start_date=None, end_date=None):
    q = (_sb().table("balance_updates")
         .select("update_date, balance")
         .eq("source_id", source_id))
    if start_date:
        q = q.gte("update_date", start_date)
    if end_date:
        q = q.lte("update_date", end_date)
    resp = q.order("update_date").order("id").execute()
    return _rows(resp.data)


def get_monthly_summary(year=None):
    resp = _sb().rpc("get_monthly_summary", {"p_year": year}).execute()
    if resp.data:
        return _rows(resp.data)
    return []


# ======================== GOLD RATES ========================

def save_gold_rate(rate_22k, rate_24k, rate_date=None):
    if rate_date is None:
        rate_date = date.today().isoformat()
    _sb().table("gold_rates").upsert({
        "rate_per_gram_22k": rate_22k, "rate_per_gram_24k": rate_24k,
        "rate_date": rate_date,
    }, on_conflict="rate_date").execute()


def get_latest_gold_rate():
    resp = (_sb().table("gold_rates").select("*")
            .order("rate_date", desc=True).limit(1).execute())
    return _row(resp.data[0]) if resp.data else None


def get_gold_rate_history():
    resp = _sb().table("gold_rates").select("*").order("rate_date").execute()
    return _rows(resp.data)


def get_gold_sources():
    resp = (_sb().table("sources").select("*")
            .eq("is_gold", True).eq("is_active", True).execute())
    return _rows(resp.data)


# ======================== GOLD PURCHASES ========================

CARAT_MULTIPLIER = {"24K": 1.0, "22K": 1.0, "18K": 1.0}


def add_gold_purchase(description, seller, weight_grams, carat, total_purchase_price,
                      purchase_date=None, note="", source_type="Physical"):
    price_per_gram = total_purchase_price / weight_grams if weight_grams > 0 else 0
    if purchase_date is None:
        purchase_date = date.today().isoformat()
    _sb().table("gold_purchases").insert({
        "description": description, "seller": seller, "weight_grams": weight_grams,
        "carat": carat, "purchase_price_per_gram": price_per_gram,
        "total_purchase_price": total_purchase_price, "purchase_date": purchase_date,
        "note": note, "source_type": source_type,
    }).execute()


def get_gold_purchases(active_only=True):
    q = _sb().table("gold_purchases").select("*")
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("purchase_date", desc=True).execute()
    return _rows(resp.data)


def update_gold_purchase(purchase_id, description, seller, weight_grams, carat,
                         total_purchase_price, purchase_date, note="", source_type="Physical"):
    price_per_gram = total_purchase_price / weight_grams if weight_grams > 0 else 0
    _sb().table("gold_purchases").update({
        "description": description, "seller": seller, "weight_grams": weight_grams,
        "carat": carat, "purchase_price_per_gram": price_per_gram,
        "total_purchase_price": total_purchase_price, "purchase_date": purchase_date,
        "note": note, "source_type": source_type,
    }).eq("id", purchase_id).execute()


def deactivate_gold_purchase(purchase_id):
    _sb().table("gold_purchases").update({"is_active": False}).eq("id", purchase_id).execute()


def get_gold_portfolio_summary():
    resp = _sb().rpc("get_gold_portfolio_summary", {}).execute()
    return _rows(resp.data) if resp.data else []


def get_gold_purchases_by_type(source_type, active_only=True):
    q = _sb().table("gold_purchases").select("*").eq("source_type", source_type)
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("purchase_date", desc=True).execute()
    return _rows(resp.data)


def get_gold_portfolio_full_summary():
    resp = _sb().rpc("get_gold_portfolio_full_summary", {}).execute()
    return _rows(resp.data) if resp.data else []


# ======================== STOCK HOLDINGS ========================

def add_stock_holding(name, ticker, market, exchange, quantity, buy_price_per_unit,
                      buy_date=None, note=""):
    currency = "USD" if market == "US" else "INR"
    total_buy_price = quantity * buy_price_per_unit
    if buy_date is None:
        buy_date = date.today().isoformat()
    _sb().table("stock_holdings").insert({
        "name": name, "ticker": ticker.upper(), "market": market, "exchange": exchange,
        "quantity": quantity, "buy_price_per_unit": buy_price_per_unit,
        "total_buy_price": total_buy_price, "currency": currency,
        "buy_date": buy_date, "note": note,
    }).execute()


def get_stock_holdings(market=None, active_only=True):
    q = _sb().table("stock_holdings").select("*")
    if active_only:
        q = q.eq("is_active", True)
    if market:
        q = q.eq("market", market)
    resp = q.order("market").order("name").execute()
    return _rows(resp.data)


def update_stock_holding(holding_id, name, ticker, market, exchange, quantity,
                         buy_price_per_unit, buy_date, note=""):
    currency = "USD" if market == "US" else "INR"
    total_buy_price = quantity * buy_price_per_unit
    _sb().table("stock_holdings").update({
        "name": name, "ticker": ticker.upper(), "market": market, "exchange": exchange,
        "quantity": quantity, "buy_price_per_unit": buy_price_per_unit,
        "total_buy_price": total_buy_price, "currency": currency,
        "buy_date": buy_date, "note": note,
    }).eq("id", holding_id).execute()


def deactivate_stock_holding(holding_id):
    _sb().table("stock_holdings").update({"is_active": False}).eq("id", holding_id).execute()


def get_stock_portfolio_summary(market=None):
    resp = _sb().rpc("get_stock_portfolio_summary", {"p_market": market}).execute()
    return _rows(resp.data) if resp.data else []


# ======================== STOCK VALUE UPDATES ========================

def add_stock_value_update(holding_id, current_price, update_date=None, note=""):
    if update_date is None:
        update_date = date.today().isoformat()
    resp = (_sb().table("stock_holdings").select("quantity")
            .eq("id", holding_id).limit(1).execute())
    qty = resp.data[0]["quantity"] if resp.data else 0
    current_value = qty * current_price
    _sb().table("stock_value_updates").insert({
        "holding_id": holding_id, "current_price": current_price,
        "current_value": current_value, "update_date": update_date, "note": note,
    }).execute()


def get_latest_stock_value(holding_id):
    resp = (_sb().table("stock_value_updates").select("*")
            .eq("holding_id", holding_id)
            .order("update_date", desc=True).order("id", desc=True)
            .limit(1).execute())
    return _row(resp.data[0]) if resp.data else None


def get_stock_value_history(holding_id):
    resp = (_sb().table("stock_value_updates").select("*")
            .eq("holding_id", holding_id)
            .order("update_date").execute())
    return _rows(resp.data)


# ======================== STOCK SELLS ========================

def sell_stock(holding_id, quantity_sold, sell_price_per_unit, sell_date=None, note=""):
    if sell_date is None:
        sell_date = date.today().isoformat()
    total_sell_price = quantity_sold * sell_price_per_unit
    _sb().table("stock_sells").insert({
        "holding_id": holding_id, "quantity_sold": quantity_sold,
        "sell_price_per_unit": sell_price_per_unit,
        "total_sell_price": total_sell_price, "sell_date": sell_date, "note": note,
    }).execute()
    # Update holding quantity
    resp = (_sb().table("stock_holdings").select("quantity, buy_price_per_unit")
            .eq("id", holding_id).limit(1).execute())
    if resp.data:
        h = resp.data[0]
        new_qty = max(0, h["quantity"] - quantity_sold)
        new_total_buy = new_qty * h["buy_price_per_unit"]
        if new_qty <= 0:
            _sb().table("stock_holdings").update({
                "quantity": 0, "total_buy_price": 0, "is_active": False,
            }).eq("id", holding_id).execute()
        else:
            _sb().table("stock_holdings").update({
                "quantity": new_qty, "total_buy_price": new_total_buy,
            }).eq("id", holding_id).execute()


def get_stock_sells(holding_id=None):
    q = _sb().table("stock_sells").select("*, stock_holdings(name, ticker, market, currency)")
    if holding_id:
        q = q.eq("holding_id", holding_id)
    resp = q.order("sell_date", desc=True).execute()
    result = []
    for r in resp.data or []:
        sh = r.pop("stock_holdings", {}) or {}
        r.update(sh)
        result.append(_DictRow(r))
    return result


def get_stock_sell_summary():
    resp = _sb().rpc("get_stock_sell_summary", {}).execute()
    return _rows(resp.data) if resp.data else []


# ======================== EXCHANGE RATES ========================

def save_exchange_rate(rate, rate_date=None, from_currency="USD", to_currency="INR"):
    if rate_date is None:
        rate_date = date.today().isoformat()
    _sb().table("exchange_rates").upsert({
        "from_currency": from_currency, "to_currency": to_currency,
        "rate": rate, "rate_date": rate_date,
    }, on_conflict="from_currency,to_currency,rate_date").execute()


def get_latest_exchange_rate(from_currency="USD", to_currency="INR"):
    resp = (_sb().table("exchange_rates").select("*")
            .eq("from_currency", from_currency).eq("to_currency", to_currency)
            .order("rate_date", desc=True).limit(1).execute())
    return _row(resp.data[0]) if resp.data else None


def get_exchange_rate_history(from_currency="USD", to_currency="INR"):
    resp = (_sb().table("exchange_rates").select("*")
            .eq("from_currency", from_currency).eq("to_currency", to_currency)
            .order("rate_date").execute())
    return _rows(resp.data)


# ======================== POLICIES ========================

def add_policy(name, provider, policy_number, policy_type, premium_amount, premium_frequency,
               sum_assured, current_value, total_premiums_paid, start_date=None,
               maturity_date=None, note=""):
    _sb().table("policies").insert({
        "name": name, "provider": provider, "policy_number": policy_number,
        "policy_type": policy_type, "premium_amount": premium_amount,
        "premium_frequency": premium_frequency, "sum_assured": sum_assured,
        "current_value": current_value, "total_premiums_paid": total_premiums_paid,
        "start_date": start_date, "maturity_date": maturity_date, "note": note,
    }).execute()


def get_policies(active_only=True):
    q = _sb().table("policies").select("*")
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("provider").order("name").execute()
    return _rows(resp.data)


def update_policy(policy_id, name, provider, policy_number, policy_type, premium_amount,
                  premium_frequency, sum_assured, current_value, total_premiums_paid,
                  start_date, maturity_date, note=""):
    _sb().table("policies").update({
        "name": name, "provider": provider, "policy_number": policy_number,
        "policy_type": policy_type, "premium_amount": premium_amount,
        "premium_frequency": premium_frequency, "sum_assured": sum_assured,
        "current_value": current_value, "total_premiums_paid": total_premiums_paid,
        "start_date": start_date, "maturity_date": maturity_date, "note": note,
    }).eq("id", policy_id).execute()


def update_policy_value(policy_id, current_value):
    _sb().table("policies").update({"current_value": current_value}).eq("id", policy_id).execute()


def deactivate_policy(policy_id):
    _sb().table("policies").update({"is_active": False}).eq("id", policy_id).execute()


def get_policies_summary():
    resp = _sb().rpc("get_policies_summary", {}).execute()
    return _rows(resp.data) if resp.data else []


# ======================== LOANS ========================

def add_loan(borrower, original_amount, lent_date=None, expected_return_date=None, note=""):
    if lent_date is None:
        lent_date = date.today().isoformat()
    _sb().table("loans").insert({
        "borrower": borrower, "original_amount": original_amount,
        "outstanding": original_amount, "lent_date": lent_date,
        "expected_return_date": expected_return_date, "note": note,
    }).execute()


def get_loans(active_only=True, status=None):
    q = _sb().table("loans").select("*")
    if active_only:
        q = q.eq("is_active", True)
    if status:
        q = q.eq("status", status)
    resp = q.order("status").order("borrower").execute()
    return _rows(resp.data)


def update_loan(loan_id, borrower, original_amount, outstanding, lent_date,
                expected_return_date, status, note=""):
    _sb().table("loans").update({
        "borrower": borrower, "original_amount": original_amount,
        "outstanding": outstanding, "lent_date": lent_date,
        "expected_return_date": expected_return_date, "status": status, "note": note,
    }).eq("id", loan_id).execute()


def deactivate_loan(loan_id):
    _sb().table("loans").update({"is_active": False}).eq("id", loan_id).execute()


def add_loan_payment(loan_id, amount, payment_date=None, note=""):
    if payment_date is None:
        payment_date = date.today().isoformat()
    _sb().table("loan_payments").insert({
        "loan_id": loan_id, "amount": amount,
        "payment_date": payment_date, "note": note,
    }).execute()
    # Update outstanding
    resp = _sb().table("loans").select("outstanding").eq("id", loan_id).limit(1).execute()
    if resp.data:
        new_outstanding = max(0, resp.data[0]["outstanding"] - amount)
        new_status = "Fully Paid" if new_outstanding == 0 else "Partially Paid"
        _sb().table("loans").update({
            "outstanding": new_outstanding, "status": new_status,
        }).eq("id", loan_id).execute()


def get_loan_payments(loan_id):
    resp = (_sb().table("loan_payments").select("*")
            .eq("loan_id", loan_id)
            .order("payment_date", desc=True).execute())
    return _rows(resp.data)


def get_loans_summary():
    resp = _sb().rpc("get_loans_summary", {}).execute()
    return _rows(resp.data) if resp.data else []


# ======================== GOLD SCHEMES ========================

def add_gold_scheme(jeweller, scheme_name, monthly_amount, total_months, start_date=None,
                    note="", months_paid=0, total_deposited=0):
    if start_date is None:
        start_date = date.today().isoformat()
    _sb().table("gold_schemes").insert({
        "jeweller": jeweller, "scheme_name": scheme_name,
        "monthly_amount": monthly_amount, "total_months": total_months,
        "months_paid": months_paid, "total_deposited": total_deposited,
        "start_date": start_date, "note": note,
    }).execute()


def get_gold_schemes(active_only=True):
    q = _sb().table("gold_schemes").select("*")
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("status").order("jeweller").execute()
    return _rows(resp.data)


def update_gold_scheme(scheme_id, jeweller, scheme_name, monthly_amount, total_months,
                       bonus_amount, start_date, maturity_date, status, note=""):
    _sb().table("gold_schemes").update({
        "jeweller": jeweller, "scheme_name": scheme_name,
        "monthly_amount": monthly_amount, "total_months": total_months,
        "bonus_amount": bonus_amount, "start_date": start_date,
        "maturity_date": maturity_date, "status": status, "note": note,
    }).eq("id", scheme_id).execute()


def deactivate_gold_scheme(scheme_id):
    _sb().table("gold_schemes").update({"is_active": False}).eq("id", scheme_id).execute()


def add_scheme_payment(scheme_id, amount, payment_date=None, note=""):
    if payment_date is None:
        payment_date = date.today().isoformat()
    resp = _sb().table("gold_schemes").select("*").eq("id", scheme_id).limit(1).execute()
    if not resp.data:
        return
    scheme = resp.data[0]
    new_months = scheme["months_paid"] + 1
    new_total = scheme["total_deposited"] + amount
    _sb().table("gold_scheme_payments").insert({
        "scheme_id": scheme_id, "amount": amount,
        "payment_date": payment_date, "month_number": new_months, "note": note,
    }).execute()
    new_status = "Matured" if new_months >= scheme["total_months"] else "Active"
    _sb().table("gold_schemes").update({
        "months_paid": new_months, "total_deposited": new_total, "status": new_status,
    }).eq("id", scheme_id).execute()


def get_scheme_payments(scheme_id):
    resp = (_sb().table("gold_scheme_payments").select("*")
            .eq("scheme_id", scheme_id)
            .order("payment_date", desc=True).execute())
    return _rows(resp.data)


def delete_scheme_payment(payment_id):
    resp = (_sb().table("gold_scheme_payments").select("*")
            .eq("id", payment_id).limit(1).execute())
    if not resp.data:
        return
    pay = resp.data[0]
    scheme_id = pay["scheme_id"]
    amount = pay["amount"]
    _sb().table("gold_scheme_payments").delete().eq("id", payment_id).execute()
    resp2 = _sb().table("gold_schemes").select("*").eq("id", scheme_id).limit(1).execute()
    if resp2.data:
        scheme = resp2.data[0]
        new_months = max(0, scheme["months_paid"] - 1)
        new_total = max(0, scheme["total_deposited"] - amount)
        new_status = "Active" if new_months < scheme["total_months"] else "Matured"
        _sb().table("gold_schemes").update({
            "months_paid": new_months, "total_deposited": new_total, "status": new_status,
        }).eq("id", scheme_id).execute()
    # Re-number remaining payments
    remaining = (_sb().table("gold_scheme_payments").select("id")
                 .eq("scheme_id", scheme_id)
                 .order("payment_date").order("id").execute())
    for idx, row in enumerate(remaining.data or [], 1):
        _sb().table("gold_scheme_payments").update({
            "month_number": idx,
        }).eq("id", row["id"]).execute()


def update_scheme_payment(payment_id, new_amount, new_date, new_note):
    resp = (_sb().table("gold_scheme_payments").select("*")
            .eq("id", payment_id).limit(1).execute())
    if not resp.data:
        return
    pay = resp.data[0]
    old_amount = pay["amount"]
    _sb().table("gold_scheme_payments").update({
        "amount": new_amount, "payment_date": new_date, "note": new_note,
    }).eq("id", payment_id).execute()
    diff = new_amount - old_amount
    if diff != 0:
        resp2 = _sb().table("gold_schemes").select("total_deposited").eq("id", pay["scheme_id"]).limit(1).execute()
        if resp2.data:
            _sb().table("gold_schemes").update({
                "total_deposited": resp2.data[0]["total_deposited"] + diff,
            }).eq("id", pay["scheme_id"]).execute()


# ======================== SYNC BALANCES ========================

def _get_source_id_by_name(name):
    resp = (_sb().table("sources").select("id")
            .eq("name", name).eq("is_active", True).limit(1).execute())
    return resp.data[0]["id"] if resp.data else None


def _sync_update_balance(source_id, new_balance, update_date):
    """Insert balance update only if value changed."""
    resp = (_sb().table("balance_updates").select("balance")
            .eq("source_id", source_id)
            .order("update_date", desc=True).order("id", desc=True)
            .limit(1).execute())
    prev = resp.data[0]["balance"] if resp.data else 0.0
    if abs(new_balance - prev) > 0.01:
        change = new_balance - prev
        _sb().table("balance_updates").insert({
            "source_id": source_id, "balance": new_balance,
            "previous_balance": prev, "change_amount": change,
            "note": "Auto-synced from tracker", "update_date": update_date,
        }).execute()


def sync_balances_from_trackers(usd_inr_rate=None):
    updated = {}
    today = date.today().isoformat()

    # 1. TATA AIA -> policies current_value
    sid = _get_source_id_by_name("TATA AIA")
    if sid:
        resp = _sb().rpc("sum_active_policy_values", {}).execute()
        val = resp.data[0]["total"] if resp.data and resp.data[0]["total"] else 0
        if val > 0:
            updated["TATA AIA"] = val
            _sync_update_balance(sid, val, today)

    # 2. Lent Out
    sid = _get_source_id_by_name("Lent Out")
    if sid:
        resp = _sb().rpc("sum_active_loan_outstanding", {}).execute()
        val = resp.data[0]["total"] if resp.data and resp.data[0]["total"] else 0
        updated["Lent Out"] = val
        _sync_update_balance(sid, val, today)

    # 3. Shares & Stocks (India)
    sid = _get_source_id_by_name("Shares & Stocks")
    if sid:
        resp = _sb().rpc("sum_stock_values", {"p_market": "India"}).execute()
        val = resp.data[0]["total"] if resp.data and resp.data[0]["total"] else 0
        updated["Shares & Stocks"] = val
        _sync_update_balance(sid, val, today)

    # 4. US Stocks
    sid = _get_source_id_by_name("US Stocks")
    if sid:
        resp = _sb().rpc("sum_stock_values", {"p_market": "US"}).execute()
        val_usd = resp.data[0]["total"] if resp.data and resp.data[0]["total"] else 0
        rate = usd_inr_rate or 1.0
        if rate == 1.0:
            er = get_latest_exchange_rate()
            if er:
                rate = er["rate"]
        val = val_usd * rate
        updated["US Stocks"] = val
        _sync_update_balance(sid, val, today)

    # 5. Gold Scheme
    sid = _get_source_id_by_name("Gold Scheme")
    if sid:
        resp = (_sb().table("gold_schemes").select("total_deposited")
                .eq("is_active", True).execute())
        val = sum(r["total_deposited"] for r in resp.data) if resp.data else 0
        updated["Gold Scheme"] = val
        _sync_update_balance(sid, val, today)

    # 6. Gold - Physical
    sid = _get_source_id_by_name("Gold - Physical")
    if sid:
        resp = (_sb().table("gold_purchases").select("total_purchase_price")
                .eq("is_active", True).neq("seller", "GPay").execute())
        val = sum(r["total_purchase_price"] for r in resp.data) if resp.data else 0
        if val > 0:
            updated["Gold - Physical"] = val
            _sync_update_balance(sid, val, today)

    # 7. Gold - GPay
    sid = _get_source_id_by_name("Gold - GPay")
    if sid:
        resp = (_sb().table("gold_purchases").select("total_purchase_price")
                .eq("is_active", True).eq("seller", "GPay").execute())
        val = sum(r["total_purchase_price"] for r in resp.data) if resp.data else 0
        updated["Gold - GPay"] = val
        _sync_update_balance(sid, val, today)

    return updated


# ======================== SIP FUNCTIONS ========================

def add_sip(fund_name, amc, folio_number, sip_amount, frequency, sip_date_day,
            start_date, end_date, category, note="",
            installments_paid=0, total_invested=0, current_value=0, units_held=0,
            investment_type="SIP"):
    _sb().table("sips").insert({
        "fund_name": fund_name, "amc": amc, "folio_number": folio_number,
        "sip_amount": sip_amount, "frequency": frequency, "sip_date_day": sip_date_day,
        "start_date": start_date, "end_date": end_date,
        "total_invested": total_invested, "current_value": current_value,
        "units_held": units_held, "installments_paid": installments_paid,
        "category": category, "note": note, "investment_type": investment_type,
    }).execute()


def get_sips(active_only=True):
    q = _sb().table("sips").select("*")
    if active_only:
        q = q.eq("is_active", True)
    resp = q.order("status").order("fund_name").execute()
    return _rows(resp.data)


def update_sip(sip_id, fund_name, amc, folio_number, sip_amount, frequency, sip_date_day,
               start_date, end_date, category, status, note="", investment_type="SIP"):
    _sb().table("sips").update({
        "fund_name": fund_name, "amc": amc, "folio_number": folio_number,
        "sip_amount": sip_amount, "frequency": frequency, "sip_date_day": sip_date_day,
        "start_date": start_date, "end_date": end_date,
        "category": category, "status": status, "note": note,
        "investment_type": investment_type,
    }).eq("id", sip_id).execute()


def update_sip_value(sip_id, current_value):
    _sb().table("sips").update({"current_value": current_value}).eq("id", sip_id).execute()


def deactivate_sip(sip_id):
    _sb().table("sips").update({"is_active": False}).eq("id", sip_id).execute()


def add_sip_payment(sip_id, amount, nav, units_purchased, payment_date=None, note=""):
    if payment_date is None:
        payment_date = date.today().isoformat()
    resp = _sb().table("sips").select("*").eq("id", sip_id).limit(1).execute()
    if not resp.data:
        return
    sip = resp.data[0]
    new_installments = sip["installments_paid"] + 1
    new_total_invested = sip["total_invested"] + amount
    new_units = sip["units_held"] + (units_purchased or 0)
    _sb().table("sip_payments").insert({
        "sip_id": sip_id, "amount": amount, "nav": nav,
        "units_purchased": units_purchased, "payment_date": payment_date,
        "installment_number": new_installments, "note": note,
    }).execute()
    _sb().table("sips").update({
        "installments_paid": new_installments, "total_invested": new_total_invested,
        "units_held": new_units,
    }).eq("id", sip_id).execute()


def get_sip_payments(sip_id):
    resp = (_sb().table("sip_payments").select("*")
            .eq("sip_id", sip_id)
            .order("payment_date", desc=True).execute())
    return _rows(resp.data)


def delete_sip_payment(payment_id):
    resp = (_sb().table("sip_payments").select("*")
            .eq("id", payment_id).limit(1).execute())
    if not resp.data:
        return
    pay = resp.data[0]
    sip_id = pay["sip_id"]
    _sb().table("sip_payments").delete().eq("id", payment_id).execute()
    resp2 = _sb().table("sips").select("*").eq("id", sip_id).limit(1).execute()
    if resp2.data:
        sip = resp2.data[0]
        new_inst = max(0, sip["installments_paid"] - 1)
        new_total = max(0, sip["total_invested"] - pay["amount"])
        new_units = max(0, sip["units_held"] - (pay["units_purchased"] or 0))
        _sb().table("sips").update({
            "installments_paid": new_inst, "total_invested": new_total,
            "units_held": new_units,
        }).eq("id", sip_id).execute()
    remaining = (_sb().table("sip_payments").select("id")
                 .eq("sip_id", sip_id)
                 .order("payment_date").order("id").execute())
    for idx, row in enumerate(remaining.data or [], 1):
        _sb().table("sip_payments").update({
            "installment_number": idx,
        }).eq("id", row["id"]).execute()


def update_sip_payment(payment_id, new_amount, new_nav, new_units, new_date, new_note):
    resp = (_sb().table("sip_payments").select("*")
            .eq("id", payment_id).limit(1).execute())
    if not resp.data:
        return
    pay = resp.data[0]
    diff_amount = new_amount - pay["amount"]
    diff_units = (new_units or 0) - (pay["units_purchased"] or 0)
    _sb().table("sip_payments").update({
        "amount": new_amount, "nav": new_nav, "units_purchased": new_units,
        "payment_date": new_date, "note": new_note,
    }).eq("id", payment_id).execute()
    if diff_amount != 0 or diff_units != 0:
        resp2 = _sb().table("sips").select("total_invested, units_held").eq("id", pay["sip_id"]).limit(1).execute()
        if resp2.data:
            _sb().table("sips").update({
                "total_invested": resp2.data[0]["total_invested"] + diff_amount,
                "units_held": resp2.data[0]["units_held"] + diff_units,
            }).eq("id", pay["sip_id"]).execute()


def add_sip_value_update(sip_id, current_value, total_invested=None, nav=None,
                         update_date=None, note="", units_held=None):
    if update_date is None:
        update_date = date.today().isoformat()
    _sb().table("sip_value_updates").insert({
        "sip_id": sip_id, "current_value": current_value,
        "total_invested": total_invested, "nav": nav,
        "update_date": update_date, "note": note,
    }).execute()
    updates = {"current_value": current_value}
    if total_invested is not None:
        updates["total_invested"] = total_invested
    if units_held is not None:
        updates["units_held"] = units_held
    _sb().table("sips").update(updates).eq("id", sip_id).execute()


def get_sip_value_history(sip_id):
    resp = (_sb().table("sip_value_updates").select("*")
            .eq("sip_id", sip_id)
            .order("update_date").execute())
    return _rows(resp.data)


def get_all_sip_value_history():
    resp = (_sb().table("sip_value_updates")
            .select("*, sips!inner(fund_name, amc, category, is_active)")
            .eq("sips.is_active", True)
            .order("update_date").execute())
    result = []
    for r in resp.data or []:
        sip = r.pop("sips", {}) or {}
        r["fund_name"] = sip.get("fund_name", "")
        r["amc"] = sip.get("amc", "")
        r["category"] = sip.get("category", "")
        result.append(_DictRow(r))
    return result


def delete_sip_value_update(update_id):
    _sb().table("sip_value_updates").delete().eq("id", update_id).execute()


def update_sip_value_update(update_id, current_value, total_invested=None,
                            update_date=None, note=None):
    updates = {"current_value": current_value}
    if total_invested is not None:
        updates["total_invested"] = total_invested
    if update_date is not None:
        updates["update_date"] = update_date
    if note is not None:
        updates["note"] = note
    _sb().table("sip_value_updates").update(updates).eq("id", update_id).execute()
