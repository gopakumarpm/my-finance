"""Seed the database with initial data from Funds1 sheet."""
import database as db
from datetime import date

INITIAL_SOURCES = [
    # (name, category, liquidity, balance, is_gold, gold_weight_grams)
    ("Kotak Bank", "Bank Account", "Liquid", 36031.03, False, 0),
    ("HDFC Chunchun", "Bank Account", "Liquid", 34946.15, False, 0),
    ("HDFC Salary Account", "Bank Account", "Liquid", 14778.05, False, 0),
    ("HDFC Nagar Road", "Bank Account", "Liquid", 9011.18, False, 0),
    ("ICICI Savings", "Bank Account", "Liquid", 20102.28, False, 0),
    ("HDFC Bindu", "Bank Account", "Liquid", 30000.00, False, 0),
    ("RD Kotak", "Fixed Deposit/RD", "Non-Liquid", 0, False, 0),
    ("FD Kotak", "Fixed Deposit/RD", "Non-Liquid", 100000.00, False, 0),
    ("RD ICICI", "Fixed Deposit/RD", "Non-Liquid", 54000.00, False, 0),
    ("ET Money - SIPs", "Mutual Funds", "Liquid", 102190.00, False, 0),
    ("K-Invest", "Mutual Funds", "Liquid", 171000.00, False, 0),
    ("I-Pru Invest", "Mutual Funds", "Liquid", 13812.10, False, 0),
    ("TATA AIA", "Insurance", "Non-Liquid", 608924.55, False, 0),
    ("Lent Out", "Receivables", "Non-Liquid", 1120250.00, False, 0),
    ("Shares & Stocks", "Equity", "Liquid", 63036.88, False, 0),
    ("US Stocks", "Equity", "Liquid", 30793.45, False, 0),
    ("ICICI Kittu", "Bank Account", "Non-Liquid", 110000.00, False, 0),
    ("Gold Scheme", "Gold", "Non-Liquid", 100000.00, True, 0),
    ("Amazon Pay", "Digital Wallet", "Liquid", 205200.00, False, 0),
    ("Gold - GPay", "Gold", "Liquid", 13683.01, True, 0),
    ("Gold - Physical", "Gold", "Non-Liquid", 3854334.00, True, 500),
]


def seed():
    db.init_db()
    existing = db.get_sources(active_only=False)
    if existing:
        print("Database already has sources. Skipping seed.")
        return

    today = date.today().isoformat()
    for name, category, liquidity, balance, is_gold, gold_wt in INITIAL_SOURCES:
        db.add_source(name, category, liquidity, is_gold, gold_wt)

    # Now add initial balances
    sources = db.get_sources()
    source_map = {s["name"]: s["id"] for s in sources}

    for name, _, _, balance, _, _ in INITIAL_SOURCES:
        if name in source_map:
            db.update_balance(source_map[name], balance, "Initial balance from Excel", today)

    print(f"Seeded {len(INITIAL_SOURCES)} sources with initial balances.")


if __name__ == "__main__":
    seed()
