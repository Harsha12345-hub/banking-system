"""
database.py - Database connection and initialization for Banking System
Uses SQLite (MySQL-compatible schema) for Replit compatibility
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "banking_system.db")


def get_db():
    """Get a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database: create tables, views, triggers, and seed data."""
    conn = get_db()
    cur = conn.cursor()

    # ─────────────────────────────────────────────
    # TABLE: BRANCH
    # ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS BRANCH (
            BranchID   INTEGER PRIMARY KEY AUTOINCREMENT,
            BranchName TEXT    NOT NULL,
            IFSCCode   TEXT    NOT NULL UNIQUE,
            Address    TEXT    NOT NULL,
            City       TEXT    NOT NULL,
            Phone      TEXT    NOT NULL
        )
    """)

    # ─────────────────────────────────────────────
    # TABLE: CUSTOMER
    # ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS CUSTOMER (
            CustomerID   INTEGER PRIMARY KEY AUTOINCREMENT,
            Name         TEXT    NOT NULL,
            DateOfBirth  TEXT    NOT NULL,
            Email        TEXT    NOT NULL UNIQUE,
            Phone        TEXT    NOT NULL,
            Address      TEXT    NOT NULL,
            AadhaarNo    TEXT    NOT NULL UNIQUE,
            CreatedAt    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ─────────────────────────────────────────────
    # TABLE: ACCOUNT
    # ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ACCOUNT (
            AccountID     INTEGER PRIMARY KEY AUTOINCREMENT,
            CustomerID    INTEGER NOT NULL,
            AccountNumber TEXT    NOT NULL UNIQUE,
            AccountType   TEXT    NOT NULL CHECK(AccountType IN ('Savings','Current','Fixed Deposit')),
            Balance       REAL    NOT NULL DEFAULT 0.00,
            OpeningDate   TEXT    NOT NULL DEFAULT (date('now')),
            Status        TEXT    NOT NULL DEFAULT 'Active' CHECK(Status IN ('Active','Frozen','Closed')),
            BranchID      INTEGER,
            FOREIGN KEY (CustomerID) REFERENCES CUSTOMER(CustomerID) ON DELETE CASCADE,
            FOREIGN KEY (BranchID)   REFERENCES BRANCH(BranchID)
        )
    """)

    # ─────────────────────────────────────────────
    # TABLE: TRANSACTIONS
    # ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS TRANSACTIONS (
            TransactionID   INTEGER PRIMARY KEY AUTOINCREMENT,
            AccountID       INTEGER NOT NULL,
            TransactionType TEXT    NOT NULL CHECK(TransactionType IN ('Deposit','Withdrawal','Transfer')),
            Amount          REAL    NOT NULL,
            TransactionDate TEXT    NOT NULL DEFAULT (datetime('now')),
            Description     TEXT,
            BalanceAfter    REAL    NOT NULL,
            FOREIGN KEY (AccountID) REFERENCES ACCOUNT(AccountID) ON DELETE CASCADE
        )
    """)

    # ─────────────────────────────────────────────
    # TABLE: LOAN
    # ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS LOAN (
            LoanID       INTEGER PRIMARY KEY AUTOINCREMENT,
            CustomerID   INTEGER NOT NULL,
            LoanType     TEXT    NOT NULL CHECK(LoanType IN ('Home','Car','Personal','Education','Business')),
            Amount       REAL    NOT NULL,
            InterestRate REAL    NOT NULL,
            StartDate    TEXT    NOT NULL DEFAULT (date('now')),
            Status       TEXT    NOT NULL DEFAULT 'Pending' CHECK(Status IN ('Pending','Approved','Rejected','Closed')),
            FOREIGN KEY (CustomerID) REFERENCES CUSTOMER(CustomerID) ON DELETE CASCADE
        )
    """)

    # ─────────────────────────────────────────────
    # TABLE: USERS (admin / employee login)
    # ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            UserID   INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT    NOT NULL UNIQUE,
            Password TEXT    NOT NULL,
            Role     TEXT    NOT NULL DEFAULT 'Employee' CHECK(Role IN ('Admin','Employee'))
        )
    """)

    # ─────────────────────────────────────────────
    # INDEX for faster lookups
    # ─────────────────────────────────────────────
    cur.execute("CREATE INDEX IF NOT EXISTS idx_account_customer ON ACCOUNT(CustomerID)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_txn_account     ON TRANSACTIONS(AccountID)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_loan_customer   ON LOAN(CustomerID)")

    # ─────────────────────────────────────────────
    # VIEW: CustomerAccountSummary
    # Joins CUSTOMER + ACCOUNT to give a combined summary
    # ─────────────────────────────────────────────
    cur.execute("DROP VIEW IF EXISTS CustomerAccountSummary")
    cur.execute("""
        CREATE VIEW CustomerAccountSummary AS
        SELECT
            c.CustomerID,
            c.Name          AS CustomerName,
            c.Email,
            c.Phone,
            a.AccountID,
            a.AccountNumber,
            a.AccountType,
            a.Balance,
            a.Status        AS AccountStatus,
            b.BranchName
        FROM CUSTOMER c
        JOIN ACCOUNT  a ON c.CustomerID = a.CustomerID
        LEFT JOIN BRANCH b ON a.BranchID = b.BranchID
    """)

    # ─────────────────────────────────────────────
    # VIEW: TransactionDetails
    # Joins TRANSACTIONS + ACCOUNT + CUSTOMER
    # ─────────────────────────────────────────────
    cur.execute("DROP VIEW IF EXISTS TransactionDetails")
    cur.execute("""
        CREATE VIEW TransactionDetails AS
        SELECT
            t.TransactionID,
            t.TransactionDate,
            t.TransactionType,
            t.Amount,
            t.BalanceAfter,
            t.Description,
            a.AccountNumber,
            c.Name   AS CustomerName,
            c.Email
        FROM TRANSACTIONS t
        JOIN ACCOUNT  a ON t.AccountID  = a.AccountID
        JOIN CUSTOMER c ON a.CustomerID = c.CustomerID
    """)

    # ─────────────────────────────────────────────
    # TRIGGER: UpdateBalanceAfterTransaction
    # Automatically updates ACCOUNT.Balance after insert into TRANSACTIONS
    # ─────────────────────────────────────────────
    cur.execute("DROP TRIGGER IF EXISTS UpdateBalanceAfterTransaction")
    cur.execute("""
        CREATE TRIGGER UpdateBalanceAfterTransaction
        AFTER INSERT ON TRANSACTIONS
        FOR EACH ROW
        BEGIN
            UPDATE ACCOUNT
            SET Balance = NEW.BalanceAfter
            WHERE AccountID = NEW.AccountID;
        END
    """)

    # ─────────────────────────────────────────────
    # SEED DATA — only if tables are empty
    # ─────────────────────────────────────────────
    if cur.execute("SELECT COUNT(*) FROM USERS").fetchone()[0] == 0:
        # Admin + Employee users (plain text passwords for demo)
        cur.executemany(
            "INSERT INTO USERS (Username, Password, Role) VALUES (?,?,?)",
            [
                ("admin",    "admin123",    "Admin"),
                ("employee", "employee123", "Employee"),
            ],
        )

    if cur.execute("SELECT COUNT(*) FROM BRANCH").fetchone()[0] == 0:
        branches = [
            ("Main Branch",      "BANK0001", "12 MG Road",          "Mumbai",     "022-11112222"),
            ("North Branch",     "BANK0002", "45 Nehru Place",       "Delhi",      "011-22223333"),
            ("South Branch",     "BANK0003", "78 Anna Salai",        "Chennai",    "044-33334444"),
            ("East Branch",      "BANK0004", "23 Park Street",       "Kolkata",    "033-44445555"),
            ("West Branch",      "BANK0005", "56 FC Road",           "Pune",       "020-55556666"),
            ("Central Branch",   "BANK0006", "89 MG Road",           "Bengaluru",  "080-66667777"),
            ("Airport Branch",   "BANK0007", "Terminal 2, Airport",  "Hyderabad",  "040-77778888"),
            ("University Branch","BANK0008", "Near University Gate", "Ahmedabad",  "079-88889999"),
            ("Tech Park Branch", "BANK0009", "Infosys Campus",       "Noida",      "0120-9999000"),
            ("Harbor Branch",    "BANK0010", "Port Trust Road",      "Kochi",      "0484-1112233"),
        ]
        cur.executemany(
            "INSERT INTO BRANCH (BranchName,IFSCCode,Address,City,Phone) VALUES (?,?,?,?,?)",
            branches,
        )

    if cur.execute("SELECT COUNT(*) FROM CUSTOMER").fetchone()[0] == 0:
        customers = [
            ("Arjun Sharma",    "1992-04-15", "arjun@gmail.com",    "9876543210", "23 Lake View, Mumbai",     "123456789012"),
            ("Priya Patel",     "1988-07-22", "priya@gmail.com",    "9765432109", "45 Rose Garden, Delhi",    "234567890123"),
            ("Rahul Mehta",     "1995-11-08", "rahul@gmail.com",    "9654321098", "78 Elm Street, Chennai",   "345678901234"),
            ("Sneha Reddy",     "1990-03-30", "sneha@gmail.com",    "9543210987", "12 Hill Top, Hyderabad",   "456789012345"),
            ("Vikram Singh",    "1985-09-14", "vikram@gmail.com",   "9432109876", "56 Birch Lane, Kolkata",   "567890123456"),
            ("Kavya Nair",      "1993-06-25", "kavya@gmail.com",    "9321098765", "89 Maple Road, Kochi",     "678901234567"),
            ("Ankit Gupta",     "1997-01-12", "ankit@gmail.com",    "9210987654", "34 Oak Drive, Pune",       "789012345678"),
            ("Pooja Joshi",     "1986-12-05", "pooja@gmail.com",    "9109876543", "67 Pine Ave, Bengaluru",   "890123456789"),
            ("Suresh Kumar",    "1991-08-18", "suresh@gmail.com",   "9087654321", "90 Cedar Blvd, Ahmedabad", "901234567890"),
            ("Meera Iyer",      "1994-02-27", "meera@gmail.com",    "9076543219", "11 Spruce St, Noida",      "012345678901"),
        ]
        cur.executemany(
            "INSERT INTO CUSTOMER (Name,DateOfBirth,Email,Phone,Address,AadhaarNo) VALUES (?,?,?,?,?,?)",
            customers,
        )

    if cur.execute("SELECT COUNT(*) FROM ACCOUNT").fetchone()[0] == 0:
        accounts = [
            (1,  "ACC1000001", "Savings",       150000.00, "2020-01-10", "Active",  1),
            (2,  "ACC1000002", "Current",        80000.00, "2019-05-20", "Active",  2),
            (3,  "ACC1000003", "Savings",       220000.00, "2021-03-15", "Active",  3),
            (4,  "ACC1000004", "Fixed Deposit", 500000.00, "2018-11-01", "Active",  4),
            (5,  "ACC1000005", "Savings",        45000.00, "2022-07-25", "Active",  5),
            (6,  "ACC1000006", "Current",       310000.00, "2020-09-10", "Active",  6),
            (7,  "ACC1000007", "Savings",        72000.00, "2021-12-05", "Frozen",  7),
            (8,  "ACC1000008", "Savings",       190000.00, "2019-08-14", "Active",  8),
            (9,  "ACC1000009", "Current",       430000.00, "2017-06-30", "Active",  9),
            (10, "ACC1000010", "Savings",        95000.00, "2023-02-18", "Active", 10),
        ]
        cur.executemany(
            "INSERT INTO ACCOUNT (CustomerID,AccountNumber,AccountType,Balance,OpeningDate,Status,BranchID) VALUES (?,?,?,?,?,?,?)",
            accounts,
        )

    if cur.execute("SELECT COUNT(*) FROM TRANSACTIONS").fetchone()[0] == 0:
        # Insert transactions and let the trigger update balances
        txns = [
            (1, "Deposit",    50000.00, "2024-01-05 10:00:00", "Initial deposit",        200000.00),
            (1, "Withdrawal", 10000.00, "2024-01-10 11:30:00", "ATM withdrawal",         190000.00),
            (2, "Deposit",    30000.00, "2024-01-08 09:15:00", "Cash deposit",           110000.00),
            (3, "Deposit",   100000.00, "2024-01-12 14:00:00", "Salary credit",          320000.00),
            (3, "Withdrawal", 20000.00, "2024-01-15 16:45:00", "Online shopping",        300000.00),
            (4, "Deposit",   200000.00, "2024-01-20 08:30:00", "FD renewal",             700000.00),
            (5, "Deposit",    15000.00, "2024-01-22 12:00:00", "Cash deposit",            60000.00),
            (6, "Transfer",   50000.00, "2024-01-25 10:30:00", "Transfer to savings",    260000.00),
            (8, "Deposit",    40000.00, "2024-01-28 15:00:00", "Dividend credit",        230000.00),
            (9, "Withdrawal", 80000.00, "2024-01-30 09:45:00", "Vendor payment",         350000.00),
            (10,"Deposit",    25000.00, "2024-02-01 11:00:00", "Birthday gift deposit",  120000.00),
            (1, "Transfer",   30000.00, "2024-02-05 13:15:00", "Transfer to ACC1000003", 160000.00),
        ]
        cur.executemany(
            "INSERT INTO TRANSACTIONS (AccountID,TransactionType,Amount,TransactionDate,Description,BalanceAfter) VALUES (?,?,?,?,?,?)",
            txns,
        )

    if cur.execute("SELECT COUNT(*) FROM LOAN").fetchone()[0] == 0:
        loans = [
            (1,  "Home",      2500000.00, 8.5,  "2021-06-01", "Approved"),
            (2,  "Car",        650000.00, 10.0, "2022-03-15", "Approved"),
            (3,  "Personal",   200000.00, 12.5, "2023-01-20", "Approved"),
            (4,  "Education",  800000.00, 7.0,  "2020-09-05", "Closed"),
            (5,  "Business",  1500000.00, 11.0, "2023-07-10", "Pending"),
            (6,  "Home",      3500000.00, 8.0,  "2019-11-25", "Approved"),
            (7,  "Car",        450000.00, 9.5,  "2024-01-08", "Pending"),
            (8,  "Personal",   100000.00, 13.0, "2023-05-12", "Rejected"),
            (9,  "Business",  2000000.00, 10.5, "2022-08-30", "Approved"),
            (10, "Education",  600000.00, 6.5,  "2024-02-14", "Pending"),
        ]
        cur.executemany(
            "INSERT INTO LOAN (CustomerID,LoanType,Amount,InterestRate,StartDate,Status) VALUES (?,?,?,?,?,?)",
            loans,
        )

    conn.commit()
    conn.close()


def transfer_money(from_account_id: int, to_account_id: int, amount: float) -> dict:
    """
    Stored-procedure equivalent: TransferMoney()
    Atomically transfers `amount` from one account to another.
    Returns {'success': bool, 'message': str}
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        # Validate source account
        src = cur.execute(
            "SELECT AccountID, Balance, Status FROM ACCOUNT WHERE AccountID=?",
            (from_account_id,),
        ).fetchone()
        if not src:
            return {"success": False, "message": "Source account not found."}
        if src["Status"] != "Active":
            return {"success": False, "message": "Source account is not active."}
        if src["Balance"] < amount:
            return {"success": False, "message": "Insufficient balance in source account."}

        # Validate destination account
        dst = cur.execute(
            "SELECT AccountID, Balance, Status FROM ACCOUNT WHERE AccountID=?",
            (to_account_id,),
        ).fetchone()
        if not dst:
            return {"success": False, "message": "Destination account not found."}
        if dst["Status"] != "Active":
            return {"success": False, "message": "Destination account is not active."}

        new_src_balance = src["Balance"] - amount
        new_dst_balance = dst["Balance"] + amount

        # Debit
        cur.execute(
            """INSERT INTO TRANSACTIONS (AccountID,TransactionType,Amount,Description,BalanceAfter)
               VALUES (?,?,?,?,?)""",
            (from_account_id, "Transfer", amount, f"Transfer to AccountID {to_account_id}", new_src_balance),
        )
        # Credit
        cur.execute(
            """INSERT INTO TRANSACTIONS (AccountID,TransactionType,Amount,Description,BalanceAfter)
               VALUES (?,?,?,?,?)""",
            (to_account_id, "Deposit", amount, f"Transfer from AccountID {from_account_id}", new_dst_balance),
        )

        conn.commit()
        return {"success": True, "message": f"₹{amount:,.2f} transferred successfully."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        conn.close()
