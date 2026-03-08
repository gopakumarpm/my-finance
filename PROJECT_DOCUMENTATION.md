# Finance Tracker - Complete Project Documentation

**Version:** 1.1
**Date:** 08 March 2026
**Author:** Gopakumar
**URL:** https://my-finance-manager.streamlit.app
**Repository:** https://github.com/gopakumarpm/my-finance

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Database Schema](#5-database-schema)
6. [Application Pages](#6-application-pages)
7. [Authentication & Security](#7-authentication--security)
8. [API Integrations](#8-api-integrations)
9. [Deployment](#9-deployment)
10. [Configuration](#10-configuration)
11. [Database Functions Reference](#11-database-functions-reference)
12. [Supabase RPC Functions](#12-supabase-rpc-functions)
13. [Maintenance & Operations](#13-maintenance--operations)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Project Overview

Finance Tracker is a personal finance management web application that consolidates and tracks all financial assets across multiple categories. It provides a unified dashboard with AI-generated insights, interactive charts, and detailed portfolio views.

### Key Features

- **Unified Dashboard** with net worth calculation, AI financial insights, portfolio allocation charts, and health scoring
- **Bank Account Tracking** with balance history, change tracking, and multi-account management
- **Digital Wallet Management** for e-wallets like Amazon Pay, Google Pay, etc.
- **Gold Portfolio** tracking physical gold, digital gold, and jeweller gold schemes with live rate integration
- **Stock & Equity Portfolio** for Indian (NSE/BSE) and US stocks with live price fetching via Yahoo Finance
- **SIP & Mutual Fund Tracking** with NAV tracking, XIRR calculation, and value history
- **Insurance Policy Management** with premium tracking, maturity timeline, and value updates
- **Loan/Lent Out Tracking** for money lent to others with payment history
- **Gold Savings Schemes** monthly payment tracking with jewellers
- **History & Analytics** with snapshots, growth trends, money movements, and comparisons
- **Data Export** full backup as Excel (.xlsx) with one sheet per table
- **4-Digit PIN Authentication** with server-side brute-force lockout
- **Mobile Responsive Design** optimized for both desktop and phone access
- **Cloud Deployment** on Streamlit Community Cloud (always-on, no laptop needed)

---

## 2. Architecture

```
+-------------------+       +--------------------+       +------------------+
|   User Browser    | HTTPS |  Streamlit Cloud   |  API  |    Supabase      |
|  (Mobile/Desktop) +------>+  (app.py running)  +------>+  PostgreSQL DB   |
|                   |       |  Python 3.12       |       |  16 tables       |
+-------------------+       +--------+-----------+       |  13 RPC funcs    |
                                     |                   |  RLS enabled     |
                            +--------+-----------+       +------------------+
                            | External APIs      |
                            | - GoodReturns.in   |
                            | - BankBazaar.com   |
                            | - Yahoo Finance    |
                            +--------------------+
```

### Data Flow

1. User authenticates with 4-digit PIN (verified against SHA-256 hash)
2. Streamlit app runs server-side on Streamlit Cloud
3. App connects to Supabase PostgreSQL using anon key (stored in secrets)
4. Database operations go through `database.py` abstraction layer
5. Live data (gold rates, stock prices, USD/INR) fetched from external APIs on demand
6. All rendering happens server-side; only HTML/WebSocket sent to browser

---

## 3. Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Frontend** | Streamlit | >= 1.30.0 |
| **Backend** | Python | 3.12.12 |
| **Database** | Supabase PostgreSQL | Cloud-hosted |
| **Charts** | Plotly | >= 5.18.0 |
| **Data Processing** | Pandas | >= 2.0.0 |
| **Gold Rates** | BeautifulSoup4 (web scraping) | >= 4.12.0 |
| **Stock Prices** | yfinance (Yahoo Finance API) | >= 0.2.0 |
| **Excel Export** | openpyxl | >= 3.1.0 |
| **HTTP Client** | requests | >= 2.31.0 |
| **DB Client** | supabase-py | >= 2.0.0 |
| **Hosting** | Streamlit Community Cloud | Free tier |
| **Tunnel (Local)** | Cloudflare Tunnel (cloudflared) | Latest |

---

## 4. Project Structure

```
app/
+-- .streamlit/
|   +-- config.toml          # Streamlit server configuration
|   +-- secrets.toml          # Credentials (gitignored)
+-- app.py                    # Main application (6,950+ lines)
+-- database.py               # Supabase database layer (934 lines)
+-- gold_rate.py              # Gold rate scraper (GoodReturns, BankBazaar)
+-- stock_price.py            # Stock price fetcher (Yahoo Finance)
+-- seed_data.py              # Initial data seeder (no-op after migration)
+-- requirements.txt          # Python dependencies
+-- start.sh                  # Local startup script
+-- deploy.sh                 # Cloudflare tunnel deployment script
+-- .gitignore                # Git exclusions
+-- VAPT_Report.pdf           # Security audit report (gitignored)
+-- PROJECT_DOCUMENTATION.md  # This file
+-- finance_tracker.db        # Legacy SQLite database (gitignored)
+-- database_sqlite.py        # Legacy SQLite database layer (gitignored)
+-- migrate_to_supabase.py    # Data migration script (gitignored)
```

### Files NOT in Repository (gitignored)

| File | Reason |
|------|--------|
| `.streamlit/secrets.toml` | Contains Supabase keys and PIN hash |
| `finance_tracker.db` | Legacy SQLite database |
| `database_sqlite.py` | Legacy SQLite code (backup) |
| `migrate_to_supabase.py` | One-time migration script |
| `VAPT_Report.pdf` | Confidential security report |
| `.venv/` | Python virtual environment |

---

## 5. Database Schema

### Supabase Project

- **Project ID:** `ihqttqxggurnahatpugm`
- **Region:** ap-south-1 (Mumbai)
- **URL:** `https://ihqttqxggurnahatpugm.supabase.co`
- **Tables:** 17 (16 data + 1 security)
- **RPC Functions:** 13
- **RLS:** Enabled on all tables

### Table: `sources`
The central table. Every financial account/asset is a "source."

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| name | TEXT | NO | - | Account/asset name |
| category | TEXT | NO | 'Other' | Bank Account, Fixed Deposit/RD, Mutual Funds, Equity, Gold, Insurance, Digital Wallet, Receivables, Crypto, Real Estate, Other |
| liquidity | TEXT | NO | 'Liquid' | Liquid or Non-Liquid |
| is_gold | BOOLEAN | NO | false | Whether this is a gold asset |
| gold_weight_grams | REAL | YES | 0 | Gold weight in grams |
| is_active | BOOLEAN | NO | true | Soft delete flag |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `balance_updates`
Tracks every balance change for sources.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| source_id | BIGINT | NO | - | FK to sources.id |
| balance | REAL | NO | - | New balance |
| previous_balance | REAL | YES | - | Previous balance |
| change_amount | REAL | YES | - | Calculated difference |
| note | TEXT | YES | - | User note |
| updated_at | TIMESTAMPTZ | NO | now() | Timestamp |
| update_date | DATE | NO | CURRENT_DATE | Date of update |

### Table: `gold_rates`
Daily gold rates (per gram).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| rate_per_gram_22k | REAL | NO | - | 22K gold rate/gram |
| rate_per_gram_24k | REAL | YES | - | 24K gold rate/gram |
| rate_date | DATE | NO | - | Rate date |
| fetched_at | TIMESTAMPTZ | NO | now() | Fetch timestamp |

### Table: `gold_purchases`
Physical and digital gold holdings.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| description | TEXT | NO | - | Item description |
| seller | TEXT | YES | - | Seller/jeweller |
| weight_grams | REAL | NO | - | Weight in grams |
| carat | TEXT | NO | '22K' | 22K or 24K |
| purchase_price_per_gram | REAL | YES | - | Price per gram at purchase |
| total_purchase_price | REAL | NO | - | Total cost |
| purchase_date | DATE | NO | CURRENT_DATE | Purchase date |
| note | TEXT | YES | - | User note |
| source_type | TEXT | NO | 'Physical' | Physical or Digital |
| is_active | BOOLEAN | NO | true | Soft delete |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `stock_holdings`
Equity/stock positions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| name | TEXT | NO | - | Company name |
| ticker | TEXT | NO | - | Stock ticker symbol |
| market | TEXT | NO | 'India' | India or US |
| exchange | TEXT | YES | '' | NSE, BSE, or empty for US |
| quantity | REAL | NO | - | Shares held |
| buy_price_per_unit | REAL | NO | - | Average buy price |
| total_buy_price | REAL | NO | - | Total invested |
| currency | TEXT | NO | 'INR' | INR or USD |
| buy_date | DATE | NO | CURRENT_DATE | Purchase date |
| note | TEXT | YES | - | User note |
| is_active | BOOLEAN | NO | true | Soft delete |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `stock_value_updates`
Point-in-time stock price snapshots.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| holding_id | BIGINT | NO | - | FK to stock_holdings.id |
| current_price | REAL | NO | - | Price per share |
| current_value | REAL | NO | - | Total current value |
| update_date | DATE | NO | CURRENT_DATE | Snapshot date |
| note | TEXT | YES | - | User note |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `stock_sells`
Stock sale transactions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| holding_id | BIGINT | NO | - | FK to stock_holdings.id |
| quantity_sold | REAL | NO | - | Shares sold |
| sell_price_per_unit | REAL | NO | - | Sale price per share |
| total_sell_price | REAL | NO | - | Total proceeds |
| sell_date | DATE | NO | CURRENT_DATE | Sale date |
| note | TEXT | YES | - | User note |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `exchange_rates`
Currency exchange rates (primarily USD/INR).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| from_currency | TEXT | NO | 'USD' | Source currency |
| to_currency | TEXT | NO | 'INR' | Target currency |
| rate | REAL | NO | - | Exchange rate |
| rate_date | DATE | NO | - | Rate date |
| fetched_at | TIMESTAMPTZ | NO | now() | Fetch timestamp |

### Table: `policies`
Insurance and investment policies.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| name | TEXT | NO | - | Policy name |
| provider | TEXT | NO | - | Insurance company |
| policy_number | TEXT | YES | - | Policy number |
| policy_type | TEXT | NO | 'Endowment' | Endowment, ULIP, Term, etc. |
| premium_amount | REAL | NO | 0 | Premium per frequency |
| premium_frequency | TEXT | NO | 'Yearly' | Monthly, Quarterly, Yearly |
| sum_assured | REAL | YES | 0 | Sum assured |
| current_value | REAL | NO | 0 | Current surrender/fund value |
| total_premiums_paid | REAL | NO | 0 | Total premiums paid so far |
| start_date | DATE | YES | - | Policy start date |
| maturity_date | DATE | YES | - | Maturity date |
| note | TEXT | YES | - | User note |
| is_active | BOOLEAN | NO | true | Soft delete |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `loans`
Money lent to others.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| borrower | TEXT | NO | - | Borrower name |
| original_amount | REAL | NO | - | Amount lent |
| outstanding | REAL | NO | - | Current outstanding |
| lent_date | DATE | NO | CURRENT_DATE | Date lent |
| expected_return_date | DATE | YES | - | Expected return date |
| status | TEXT | NO | 'Active' | Active, Partial, Settled |
| note | TEXT | YES | - | User note |
| is_active | BOOLEAN | NO | true | Soft delete |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `loan_payments`
Repayments received on loans.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| loan_id | BIGINT | NO | - | FK to loans.id |
| amount | REAL | NO | - | Payment amount |
| payment_date | DATE | NO | CURRENT_DATE | Payment date |
| note | TEXT | YES | - | User note |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `gold_schemes`
Monthly gold savings schemes with jewellers.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| jeweller | TEXT | NO | - | Jeweller name |
| scheme_name | TEXT | YES | - | Scheme name |
| monthly_amount | REAL | NO | - | Monthly deposit amount |
| total_months | INTEGER | NO | 11 | Total scheme duration |
| months_paid | INTEGER | NO | 0 | Months paid so far |
| total_deposited | REAL | NO | 0 | Total amount deposited |
| bonus_amount | REAL | NO | 0 | Bonus/cashback amount |
| start_date | DATE | YES | - | Scheme start date |
| maturity_date | DATE | YES | - | Maturity date |
| status | TEXT | NO | 'Active' | Active, Completed, Cancelled |
| note | TEXT | YES | - | User note |
| is_active | BOOLEAN | NO | true | Soft delete |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `gold_scheme_payments`
Individual monthly payments into gold schemes.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| scheme_id | BIGINT | NO | - | FK to gold_schemes.id |
| amount | REAL | NO | - | Payment amount |
| payment_date | DATE | NO | CURRENT_DATE | Payment date |
| month_number | INTEGER | YES | - | Which month (1-11) |
| note | TEXT | YES | - | User note |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `sips`
SIP and Mutual Fund investments.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| fund_name | TEXT | NO | - | Mutual fund name |
| amc | TEXT | YES | - | AMC/platform name |
| folio_number | TEXT | YES | - | Folio number |
| sip_amount | REAL | NO | - | SIP amount per installment |
| frequency | TEXT | NO | 'Monthly' | Payment frequency |
| sip_date_day | INTEGER | YES | 1 | SIP debit day of month |
| start_date | DATE | YES | - | SIP start date |
| end_date | DATE | YES | - | SIP end date |
| total_invested | REAL | NO | 0 | Total invested |
| current_value | REAL | NO | 0 | Current market value |
| units_held | REAL | NO | 0 | Total units held |
| installments_paid | INTEGER | NO | 0 | Number of installments |
| status | TEXT | NO | 'Active' | Active, Paused, Completed |
| category | TEXT | NO | 'Equity' | Equity, Debt, Hybrid, etc. |
| investment_type | TEXT | NO | 'SIP' | SIP or Lumpsum |
| note | TEXT | YES | - | User note |
| is_active | BOOLEAN | NO | true | Soft delete |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `sip_payments`
Individual SIP installment payments.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| sip_id | BIGINT | NO | - | FK to sips.id |
| amount | REAL | NO | - | Payment amount |
| nav | REAL | YES | - | NAV at purchase |
| units_purchased | REAL | YES | - | Units bought |
| payment_date | DATE | NO | CURRENT_DATE | Payment date |
| installment_number | INTEGER | YES | - | Installment sequence |
| note | TEXT | YES | - | User note |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `sip_value_updates`
Point-in-time SIP/MF value snapshots.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| sip_id | BIGINT | NO | - | FK to sips.id |
| current_value | REAL | NO | - | Current market value |
| total_invested | REAL | YES | - | Total invested at snapshot |
| nav | REAL | YES | - | NAV at snapshot |
| update_date | DATE | NO | CURRENT_DATE | Snapshot date |
| note | TEXT | YES | - | User note |
| created_at | TIMESTAMPTZ | NO | now() | Creation timestamp |

### Table: `login_lockout` (Security)
Server-side login attempt tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | BIGSERIAL | NO | auto | Primary key |
| ip_key | TEXT | NO | 'global' | Lockout key |
| attempts | INTEGER | NO | 0 | Failed attempts count |
| locked_until | TIMESTAMPTZ | YES | - | Lockout expiry time |
| updated_at | TIMESTAMPTZ | YES | now() | Last update |

### Entity Relationship Diagram

```
sources (1) ---< balance_updates (many)

gold_schemes (1) ---< gold_scheme_payments (many)

stock_holdings (1) ---< stock_value_updates (many)
stock_holdings (1) ---< stock_sells (many)

loans (1) ---< loan_payments (many)

sips (1) ---< sip_payments (many)
sips (1) ---< sip_value_updates (many)

gold_purchases (standalone)
gold_rates (standalone)
exchange_rates (standalone)
policies (standalone)
login_lockout (standalone)
```

---

## 6. Application Pages

### Dashboard
- **Hero Banner** with net worth, liquid/non-liquid split, month-over-month change, active sources count
- **Portfolio Cards** (clickable) showing value, source count, percentage, and change indicator for each active asset class
- **AI Financial Advisor** card with insights on diversification, liquidity, growth momentum, risk profile, concentration risk, gold allocation, and savings opportunities
- **Tabs:**
  - **Overview:** Health score gauge, composition breakdown, allocation pie chart, top holdings table, liquidity/risk analysis
  - **Analytics:** Net worth trend line, monthly bar chart, category distribution
  - **Deep Dive:** Category selector with detailed breakdown, pie chart, and navigation to portfolio pages

### Bank Update
- Account cards with current balance, last change, and update date
- Balance update form with new balance, note, and date
- Balance history table for each account
- Quick view of all bank balances
- Insights: largest account, zero-balance alerts

### Digital Wallet
- Wallet cards with balance and last update
- Balance update form
- History table per wallet
- Quick view and insights

### Gold Portfolio
- **Auto-fetching gold rates:** On page load, automatically fetches today's Pune gold rate from GoodReturns.in (BankBazaar.com fallback) if the stored rate is stale. Manual fetch/entry still available.
- **Overview tab:** Hero banner with total portfolio value, gain/loss, total invested, total weight, current 22K/24K rates. Portfolio breakdown cards (Physical, Digital, Schemes). Allocation bar chart. AI-driven portfolio insights.
- **Physical Gold tab:**
  - **Add form** with auto-calculated Total Price (weight × today's rate for selected purity). Price reactively updates when weight or purity changes. User can override with actual purchase price.
  - **Vault summary card** showing current value (based on today's rate), total invested, total weight, and gain/loss with percentage.
  - **Per-item cards** with current market value as the primary display, purchase price below, gain/loss amount and %, buy vs current rate per gram comparison. Left border color reflects gain (green) or loss (red).
  - Edit/delete individual holdings.
- **Digital Gold tab:**
  - **Add form** with auto-calculated price (weight × 24K rate). Reactively updates on weight change.
  - **Vault summary card** with current value, invested, weight, gain/loss.
  - **Per-item cards** with same enhanced layout as Physical Gold.
  - Edit/delete individual holdings.
- **Gold Schemes tab:** Active/completed scheme cards with progress bars, payment tracker, monthly commitment, total deposited. Record/edit payments.
- **Rates & History tab:** Historical rate chart, rate table, manual rate entry.

### Gold Schemes (Standalone Page)
- **Overview tab:** Active/completed scheme cards with progress bars, payment tracker, monthly commitment, total deposited
- **Record Payment tab:** Select scheme, enter amount, record monthly payment
- **Payment History tab:** All payments for selected scheme, edit/delete capability
- **Insights:** Completion rate, next payments due, total commitment

### Shares & Stock
- **Indian Stocks tab:** Holdings cards with ticker, exchange, quantity, buy/current price, P&L; live price refresh; add/sell/edit
- **US Stocks tab:** Same layout for US market stocks with USD/INR conversion
- **Value History tab:** Historical value updates for each holding
- **Sell History tab:** Past sell transactions with realized P&L
- Insights: Best/worst performers, total invested vs current value

### SIP & MF Portfolio
- **Overview tab:** Platform and category breakdowns, total invested/current value, returns percentage
- **Fund Details tab:** Individual fund cards (AMC, folio, SIP amount, units, NAV, value, P&L)
- **Update Values tab:** Bulk or individual value updates with NAV
- **Payment History tab:** SIP installment records
- **Value History tab:** Historical value snapshots per fund
- Insights: Best/worst funds, platform allocation

### Policies
- **Overview tab:** Provider breakdown, maturity timeline, total value vs premiums paid
- **Policy Details tab:** Detailed cards (provider, type, number, premium, frequency, sum assured, current value, maturity date)
- Add/edit/deactivate policies, update current values

### Lent Out
- Active loan cards (borrower, amount, outstanding, status, expected return date)
- Record repayments with date and note
- Payment history per loan
- Insights: Total outstanding, overdue loans

### History & Analytics
- **Snapshot tab:** Date-based portfolio snapshot showing all source balances on a specific date, grouped by category
- **Growth Trends tab:** Net worth trend over time, category-wise growth
- **Money Movements tab:** Recent balance changes, activity feed, movement insights
- **Compare tab:** Period comparison with winners/losers and change amounts

### Manage Sources
- **Active Sources tab:** Grouped by category, edit name/category/liquidity/gold settings, deactivate
- **Add New Source tab:** Create new source with all fields
- **Inactive Sources tab:** View deactivated sources
- **Data Export:** Download full database backup as Excel (.xlsx)

---

## 7. Authentication & Security

### PIN Authentication
- 4-digit numeric PIN required on every new session
- PIN stored as SHA-256 hash in Streamlit Cloud secrets
- Hash never sent to client; verification happens server-side

### Brute Force Protection
- Maximum 5 failed attempts before 15-minute lockout
- Lockout state stored in Supabase `login_lockout` table (server-side)
- Persists across browser sessions, tabs, and devices
- Lockout timer displayed to user with countdown

### Fail-Closed Design
- If `PIN_HASH` secret is empty or missing, access is blocked (not granted)
- No authentication bypass possible through configuration error

### XSS Prevention
- All user-supplied data HTML-escaped via `_esc()` helper before rendering
- Applied to ~100 interpolation points across all pages

### Server Configuration
- XSRF (CSRF) protection enabled
- CORS enforcement enabled
- Server bound to 127.0.0.1 (localhost only for local runs)
- Streamlit Cloud handles HTTPS and network security

### Supabase Security
- Row Level Security (RLS) enabled on all 17 tables
- Anon key stored only in Streamlit Cloud secrets (never in code or browser)
- Streamlit runs server-side, so database credentials never reach the client

### Security Report
- Full VA/PT report available at `VAPT_Report.pdf` (11 pages)
- 15 findings identified: 3 Critical, 4 High, 5 Medium, 3 Low
- 14 of 15 remediated (93%); 1 accepted with justification

---

## 8. API Integrations

### Gold Rates (gold_rate.py)

**Primary Source:** GoodReturns.in
- Scrapes `https://www.goodreturns.in/gold-rates/pune.html`
- Extracts 22K and 24K per-gram rates for Pune
- Uses browser User-Agent header

**Fallback Source:** BankBazaar.com
- Scrapes `https://www.bankbazaar.com/gold-rate-pune.html`
- Used when GoodReturns is unavailable

**Auto-Fetch:** On Gold Portfolio page load, the app checks if the stored rate is from today. If stale (from a previous day or missing), it automatically fetches the live rate and saves it. This ensures vault values and gain/loss calculations always use the latest rate without manual intervention.

**Returns:**
```python
{
    "rate_22k": 15000.00,
    "rate_24k": 16364.00,
    "date": "2026-03-08",
    "source": "GoodReturns.in"
}
```

### Stock Prices (stock_price.py)

**Source:** Yahoo Finance via `yfinance` library

**Functions:**
- `fetch_stock_price(ticker, market, exchange)` - Single stock price
- `fetch_stock_prices_batch(holdings)` - Batch fetch for multiple stocks
- `fetch_usd_inr_rate()` - USD to INR exchange rate

**Ticker Formats:**
- Indian NSE: `TICKER.NS` (e.g., `RELIANCE.NS`)
- Indian BSE: `TICKER.BO` (e.g., `RELIANCE.BO`)
- US: `TICKER` (e.g., `AAPL`)
- Exchange rate: `USDINR=X`

---

## 9. Deployment

### Streamlit Community Cloud (Production)

**URL:** https://my-finance-manager.streamlit.app

**Setup:**
1. Code lives in public GitHub repo: `gopakumarpm/my-finance`
2. Streamlit Cloud deploys from `main` branch, running `app.py`
3. Secrets configured in Streamlit Cloud dashboard (not in code)

**Required Secrets:**
```toml
SUPABASE_URL = "https://ihqttqxggurnahatpugm.supabase.co"
SUPABASE_KEY = "<anon-key>"
PIN_HASH = "<sha256-hash-of-your-pin>"
```

**Auto-deploy:** Pushes to `main` branch trigger automatic redeployment.

### Local Development

```bash
cd /Users/gopakumar/Projects/My\ Finance/app
source .venv/bin/activate
streamlit run app.py
```

Access at: `http://localhost:8501`

### Local Network Access (start.sh)

```bash
./start.sh
```
Access from other devices on same WiFi via: `http://<local-ip>:8501`

### Public Access via Cloudflare Tunnel (deploy.sh)

```bash
./deploy.sh
```
Creates a temporary public HTTPS URL via Cloudflare Tunnel (free, no account needed). URL changes each restart.

---

## 10. Configuration

### .streamlit/config.toml

```toml
[server]
headless = true          # No browser auto-open
address = "127.0.0.1"   # Localhost only (security)
port = 8501              # Default Streamlit port
enableCORS = true        # Cross-origin protection
enableXsrfProtection = true  # CSRF protection

[browser]
gatherUsageStats = false  # No telemetry

[theme]
base = "light"           # Light theme
```

### .streamlit/secrets.toml (gitignored)

```toml
SUPABASE_URL = "https://ihqttqxggurnahatpugm.supabase.co"
SUPABASE_KEY = "<your-anon-key>"
PIN_HASH = "<sha256-hash>"
```

### Generating a PIN Hash

```python
import hashlib
pin = "1234"  # Your chosen PIN
print(hashlib.sha256(pin.encode()).hexdigest())
```

---

## 11. Database Functions Reference

### Source Management
| Function | Description |
|----------|-------------|
| `init_db()` | No-op (tables managed via Supabase) |
| `add_source(name, category, liquidity, is_gold, gold_weight_grams)` | Create new financial source |
| `get_sources(active_only=True)` | List all sources |
| `update_source(source_id, name, category, liquidity, is_gold, gold_weight_grams)` | Update source details |
| `deactivate_source(source_id)` | Soft-delete a source |

### Balance Tracking
| Function | Description |
|----------|-------------|
| `get_latest_balance(source_id, _retries=2)` | Get most recent balance for a source (retries on network errors) |
| `update_balance(source_id, new_balance, note, update_date)` | Record new balance |
| `get_balance_history(source_id, start_date, end_date)` | Get balance change history |
| `get_snapshot_on_date(target_date)` | Portfolio snapshot on specific date (RPC) |
| `get_daily_totals(start_date, end_date)` | Daily total balance (RPC) |
| `get_source_daily_balances(source_id, start_date, end_date)` | Daily balance for one source |
| `get_monthly_summary(year)` | Monthly net worth summary (RPC) |

### Gold
| Function | Description |
|----------|-------------|
| `save_gold_rate(rate_22k, rate_24k, rate_date)` | Save gold rate (upsert) |
| `get_latest_gold_rate()` | Most recent gold rate |
| `get_gold_rate_history()` | All gold rate records |
| `get_gold_sources()` | Sources marked as gold |
| `add_gold_purchase(...)` | Add gold holding |
| `get_gold_purchases(active_only)` | List gold holdings |
| `update_gold_purchase(...)` | Update gold holding |
| `deactivate_gold_purchase(purchase_id)` | Soft-delete gold holding |
| `get_gold_portfolio_summary()` | Aggregated gold summary (RPC) |
| `get_gold_purchases_by_type(source_type, active_only)` | Filter by Physical/Digital |
| `get_gold_portfolio_full_summary()` | Detailed portfolio breakdown (RPC) |

### Stocks
| Function | Description |
|----------|-------------|
| `add_stock_holding(...)` | Add stock position |
| `get_stock_holdings(market, active_only)` | List holdings |
| `update_stock_holding(...)` | Update holding details |
| `deactivate_stock_holding(holding_id)` | Soft-delete holding |
| `get_stock_portfolio_summary(market)` | Portfolio summary (RPC) |
| `add_stock_value_update(holding_id, current_price, update_date, note)` | Record price snapshot |
| `get_latest_stock_value(holding_id)` | Latest price for holding |
| `get_stock_value_history(holding_id)` | Price history |
| `sell_stock(holding_id, quantity_sold, sell_price_per_unit, sell_date, note)` | Record stock sale |
| `get_stock_sells(holding_id)` | Sale transactions |
| `get_stock_sell_summary()` | Aggregated sell P&L (RPC) |

### Exchange Rates
| Function | Description |
|----------|-------------|
| `save_exchange_rate(rate, rate_date, from_currency, to_currency)` | Save rate (upsert) |
| `get_latest_exchange_rate(from_currency, to_currency)` | Latest rate |
| `get_exchange_rate_history(from_currency, to_currency)` | Rate history |

### Policies
| Function | Description |
|----------|-------------|
| `add_policy(...)` | Add insurance policy |
| `get_policies(active_only)` | List policies |
| `update_policy(...)` | Update policy details |
| `update_policy_value(policy_id, current_value)` | Update current value |
| `deactivate_policy(policy_id)` | Soft-delete policy |
| `get_policies_summary()` | Aggregated summary (RPC) |

### Loans
| Function | Description |
|----------|-------------|
| `add_loan(borrower, original_amount, lent_date, expected_return_date, note)` | Add loan |
| `get_loans(active_only, status)` | List loans |
| `update_loan(...)` | Update loan details |
| `deactivate_loan(loan_id)` | Soft-delete loan |
| `add_loan_payment(loan_id, amount, payment_date, note)` | Record repayment |
| `get_loan_payments(loan_id)` | Payment history |
| `get_loans_summary()` | Aggregated summary (RPC) |

### Gold Schemes
| Function | Description |
|----------|-------------|
| `add_gold_scheme(...)` | Add scheme |
| `get_gold_schemes(active_only)` | List schemes |
| `update_gold_scheme(...)` | Update scheme details |
| `deactivate_gold_scheme(scheme_id)` | Soft-delete scheme |
| `add_scheme_payment(scheme_id, amount, payment_date, note)` | Record monthly payment |
| `get_scheme_payments(scheme_id)` | Payment history |
| `delete_scheme_payment(payment_id)` | Delete payment |
| `update_scheme_payment(payment_id, new_amount, new_date, new_note)` | Edit payment |

### SIPs / Mutual Funds
| Function | Description |
|----------|-------------|
| `add_sip(...)` | Add SIP/MF |
| `get_sips(active_only)` | List SIPs |
| `update_sip(...)` | Update SIP details |
| `update_sip_value(sip_id, current_value)` | Quick value update |
| `deactivate_sip(sip_id)` | Soft-delete SIP |
| `add_sip_payment(...)` | Record installment |
| `get_sip_payments(sip_id)` | Payment history |
| `delete_sip_payment(payment_id)` | Delete payment |
| `update_sip_payment(...)` | Edit payment |
| `add_sip_value_update(...)` | Record value snapshot |
| `get_sip_value_history(sip_id)` | Value history for one SIP |
| `get_all_sip_value_history()` | All SIP value snapshots |
| `delete_sip_value_update(update_id)` | Delete snapshot |
| `update_sip_value_update(...)` | Edit snapshot |

### Sync & Export
| Function | Description |
|----------|-------------|
| `sync_balances_from_trackers(usd_inr_rate)` | Auto-sync source balances from portfolio trackers |
| `export_all_data()` | Export all 16 tables as dict for backup |

---

## 12. Supabase RPC Functions

These PostgreSQL functions run server-side for complex queries.

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `get_snapshot_on_date` | target_date | records | All source balances on a specific date using LATERAL JOIN |
| `get_daily_totals` | start_date, end_date | records | Daily total balance across all sources |
| `get_monthly_summary` | target_year | records | Monthly net worth aggregation |
| `get_gold_portfolio_summary` | - | records | Total gold weight, value, purchase cost |
| `get_gold_portfolio_full_summary` | - | records | Detailed gold breakdown by type |
| `get_stock_portfolio_summary` | - | records | Stock portfolio totals |
| `get_stock_sell_summary` | - | records | Realized P&L from stock sales |
| `get_policies_summary` | - | records | Policy totals and value |
| `get_loans_summary` | - | records | Loan totals and outstanding |
| `sum_active_policy_values` | - | real | Sum of active policy current values |
| `sum_active_loan_outstanding` | - | real | Sum of active loan outstanding |
| `sum_stock_values` | market | real | Sum of latest stock values |
| `reset_sequence` | t_name | void | Reset auto-increment to max(id)+1 |

---

## 13. Maintenance & Operations

### Updating the Application

1. Edit code locally in `/Users/gopakumar/Projects/My Finance/app/`
2. Test locally: `streamlit run app.py`
3. Commit and push:
   ```bash
   git add <files>
   git commit -m "Description of changes"
   git push
   ```
4. Streamlit Cloud auto-deploys within ~2 minutes

### Data Backup

1. Go to **Manage Sources** page in the app
2. Scroll to bottom and click **"Download Full Backup (.xlsx)"**
3. Click **"Click to Save"** to download the Excel file
4. File contains one sheet per table with all data

### Changing the PIN

1. Generate new hash:
   ```python
   import hashlib
   print(hashlib.sha256("NEWPIN".encode()).hexdigest())
   ```
2. Update in Streamlit Cloud: Settings > Secrets > change `PIN_HASH`
3. The app will use the new PIN on next session

### Adding a New Financial Source

1. Go to **Manage Sources > Add New Source**
2. Enter name, category, liquidity type, gold flag if applicable
3. Go to the relevant portfolio page to start tracking

### Database Management

- **Supabase Dashboard:** https://supabase.com/dashboard/project/ihqttqxggurnahatpugm
- **Table Editor:** View/edit data directly in Supabase UI
- **SQL Editor:** Run custom queries
- **Backups:** Supabase provides point-in-time recovery on paid plans

---

## 14. Troubleshooting

### App Won't Load

- Check Streamlit Cloud logs at: https://share.streamlit.io (manage app > logs)
- Verify secrets are configured correctly
- Check if Supabase project is active (not paused)

### "Incorrect PIN" but PIN is Correct

- Verify PIN_HASH matches: run `hashlib.sha256("YOURPIN".encode()).hexdigest()` and compare
- Check if locked out (wait 15 minutes or reset `login_lockout` table in Supabase)

### Gold Rate Not Fetching

- Gold rates now auto-fetch on Gold Portfolio page load when stale
- GoodReturns.in may have changed their HTML structure
- Check if the site is accessible from Streamlit Cloud's region
- Fallback to BankBazaar.com happens automatically
- If auto-fetch fails, the last known rate is used; you can also enter rates manually from the Overview tab

### Stock Price Shows None

- Verify ticker symbol is correct (e.g., RELIANCE for NSE, not RELIANCE.NS)
- Yahoo Finance may be temporarily unavailable
- US tickers use plain symbol (AAPL, MSFT)

### Balance Not Updating on Dashboard

- Dashboard auto-syncs from portfolio trackers on load
- Check if `sync_balances_from_trackers()` has the correct USD/INR rate
- Verify the source is marked as active

### Supabase Connection Error / httpx.ReadError

- `get_latest_balance` now has built-in retry logic (2 retries with 0.5s delay) to handle transient `httpx.ReadError` from Supabase
- If errors persist, check if Supabase project is active: https://supabase.com/dashboard
- Verify `SUPABASE_URL` and `SUPABASE_KEY` in secrets
- Free tier pauses after 1 week of inactivity

### Resetting Login Lockout

If locked out, run in Supabase SQL Editor:
```sql
UPDATE login_lockout SET attempts = 0, locked_until = NULL WHERE ip_key = 'global';
```

---

*Document generated: 08 March 2026*
