# NexaBank — Banking Management System

A complete, fully-functional Banking Management System built with **Python Flask** and **SQLite** (MySQL-compatible schema), featuring a modern Bootstrap 5 UI.

---

## Tech Stack

| Layer    | Technology                              |
|----------|-----------------------------------------|
| Frontend | HTML5, CSS3, Bootstrap 5, Chart.js      |
| Backend  | Python 3.11, Flask 3.0                  |
| Database | SQLite (MySQL-compatible DDL)           |
| Auth     | Flask session-based authentication      |

---

## Run on Replit

The app starts automatically via the **Banking System** workflow.

**Manual start:**
```bash
cd artifacts/banking-system
python app.py
```

The app listens on port **5000**.

---

## Login Credentials

| Role     | Username  | Password     |
|----------|-----------|--------------|
| Admin    | admin     | admin123     |
| Employee | employee  | employee123  |

---

## Project Structure

```
artifacts/banking-system/
├── app.py              # Flask app factory & blueprint registration
├── database.py         # DB init, views, triggers, stored-proc equivalent
├── requirements.txt    # Python dependencies
├── README.md
│
├── routes/
│   ├── auth.py         # Login / logout
│   ├── dashboard.py    # KPI aggregates, charts data
│   ├── customers.py    # Customer CRUD
│   ├── accounts.py     # Account management (uses CustomerAccountSummary VIEW)
│   ├── transactions.py # Deposit, withdraw, fund transfer
│   ├── loans.py        # Loan application & approval
│   ├── branches.py     # Branch CRUD
│   └── reports.py      # Analytics & SQL reports
│
├── templates/
│   ├── base.html       # Sidebar + topbar layout
│   ├── login.html      # Login page
│   ├── dashboard.html  # KPI cards + charts
│   ├── customers.html  # Customer management
│   ├── accounts.html   # Account management
│   ├── transactions.html
│   ├── loans.html
│   ├── branches.html
│   └── reports.html    # Tabbed reports (5 tabs)
│
└── static/
    ├── css/style.css   # Complete banking UI theme
    └── js/main.js      # Sidebar toggle, animations, utilities
```

---

## Database Schema

```
BRANCH      ← referenced by ACCOUNT
CUSTOMER    ← referenced by ACCOUNT, LOAN
ACCOUNT     ← referenced by TRANSACTIONS
TRANSACTIONS
LOAN
USERS       ← app login table
```

---

## SQL Features Implemented

### Tables (5 core + 1 auth)
- `BRANCH`, `CUSTOMER`, `ACCOUNT`, `TRANSACTIONS`, `LOAN`, `USERS`
- Primary keys, foreign keys, CHECK constraints, UNIQUE constraints

### Indexes
```sql
CREATE INDEX idx_account_customer ON ACCOUNT(CustomerID);
CREATE INDEX idx_txn_account      ON TRANSACTIONS(AccountID);
CREATE INDEX idx_loan_customer    ON LOAN(CustomerID);
```

### Views
```sql
-- CustomerAccountSummary: JOIN CUSTOMER + ACCOUNT + BRANCH
CREATE VIEW CustomerAccountSummary AS ...

-- TransactionDetails: JOIN TRANSACTIONS + ACCOUNT + CUSTOMER
CREATE VIEW TransactionDetails AS ...
```

### Trigger
```sql
-- Automatically updates ACCOUNT.Balance after each TRANSACTIONS insert
CREATE TRIGGER UpdateBalanceAfterTransaction
AFTER INSERT ON TRANSACTIONS
FOR EACH ROW
BEGIN
    UPDATE ACCOUNT SET Balance = NEW.BalanceAfter WHERE AccountID = NEW.AccountID;
END;
```

### Stored Procedure Equivalent
```python
# database.py → transfer_money(from_id, to_id, amount)
# Atomic debit + credit wrapped in a transaction
```

### Aggregate Functions (used in Reports)
- `COUNT(*)`, `SUM(Balance)`, `AVG(Amount)`, `MAX(Balance)`
- Monthly summaries, loan type breakdowns

### Subqueries (used in Reports → Insights tab)
- Customers with balance above average
- Accounts with no recent transactions (last 90 days)

### Joins
- `CustomerAccountSummary` view uses INNER + LEFT JOINs
- `TransactionDetails` view joins 3 tables
- Dashboard top-customers query joins CUSTOMER + ACCOUNT

---

## Pages

| Route            | Description                                      |
|------------------|--------------------------------------------------|
| `/login`         | Username/password login with demo credential hints |
| `/dashboard`     | KPI cards, bar chart, pie chart, recent transactions |
| `/customers`     | Add / edit / delete customers with search         |
| `/accounts`      | View accounts via `CustomerAccountSummary` VIEW; freeze/activate |
| `/transactions`  | Deposit, withdraw, fund transfer; trigger fires on every insert |
| `/loans`         | Apply, approve/reject/close loans                |
| `/branches`      | Card + table view of branches; add/edit/delete   |
| `/reports`       | 5-tab report: Transactions, Monthly, Customers, Loans, Insights |

---

## Sample Data

10 records pre-loaded in every table:
- 10 Customers
- 10 Accounts (across all 3 types)
- 12 Transactions
- 10 Loans
- 10 Branches

---

## Setup Guide (Local)

```bash
# 1. Clone and enter directory
cd artifacts/banking-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install flask==3.0.3 werkzeug==3.0.3

# 4. Run the app
python app.py

# 5. Open browser
#    http://localhost:5000
```

The SQLite database (`banking_system.db`) is created automatically on first run.
