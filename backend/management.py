import sqlite3
from datetime import datetime

class Spent:
    def __init__(self, amount: float, category: str, money):
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        self.amount = amount
        self.date = datetime.now().strftime('%Y-%m-%d')

        # Verify the category exists
        categories = [cat[1] for cat in money.fetch_categories()]  # cat = (id, name)
        if category not in categories:
            raise ValueError(f"Invalid category: {category}")
        self.category = category

    def dic(self):
        return {'date': self.date, 'amount': f'${self.amount}', 'category': self.category}


class Money:
    def __init__(self, user_id: int):
        self.db_name = 'expenses.db'
        self.user_id = user_id
        self.initialize_db()
        self.initialize_preexisting_categories()

    def initialize_db(self):
        """Create the expenses, categories, and income tables if they don't exist."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        # Create expenses table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Create categories table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, -- NULL for preexisting categories
                name TEXT NOT NULL UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Create income table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS income (
                user_id INTEGER PRIMARY KEY,
                amount REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        conn.commit()
        conn.close()

    def initialize_preexisting_categories(self):
        preexisting_categories = [
            "Food", "Rent", "Transportation", "Utilities", "Insurance",
            "Healthcare", "Saving", "Investment", "Recreation"
        ]
        
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        
        # Delete lowercase categories
        lowercase_categories = [cat.lower() for cat in preexisting_categories]
        cur.execute("DELETE FROM categories WHERE LOWER(name) IN ({}) AND name != ?".format(
            ','.join(['?'] * len(lowercase_categories))), 
            lowercase_categories + [preexisting_categories[0]]
        )
        
        # Insert or update the proper capitalized categories
        for category in preexisting_categories:
            cur.execute("INSERT OR IGNORE INTO categories (user_id, name) VALUES (NULL, ?)", (category,))
        
        conn.commit()
        conn.close()

    def update_income(self, income: float):
        """Update or insert income for the user."""
        if income <= 0:
            raise ValueError("Income must be a positive number.")

        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO income (user_id, amount)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET amount=excluded.amount
            """,
            (self.user_id, income)
        )

        conn.commit()
        conn.close()

    def fetch_income(self):
        """Fetch the user's current income."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        cur.execute("SELECT amount FROM income WHERE user_id = ?", (self.user_id,))
        result = cur.fetchone()

        conn.close()
        return result[0] if result else 0.0

    def add_custom_category(self, category_name: str):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO categories (user_id, name) VALUES (?, ?)",
                (self.user_id, category_name)
            )
            conn.commit()
            print(f"Category '{category_name}' added successfully!")
        except sqlite3.IntegrityError:
            print("Category already exists.")
        finally:
            conn.close()

    def delete_category(self, category_name: str):
        """Delete any category."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM categories WHERE name = ?",
                (category_name,)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"ERROR deleting: {e}")
            raise
        finally:
            conn.close()

    def delete_transaction(self, transaction_id: int):
        """Delete a transaction by its ID."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM expenses WHERE id = ? AND user_id = ?",
                (transaction_id, self.user_id)
            )
            conn.commit()
            print(f"Transaction {transaction_id} was deleted.")
        except sqlite3.Error as e:
            print(f"ERROR deleting transaction: {e}")
        finally:
            conn.close()

    def fetch_categories(self):
        """Returns a list of (id, name) for all categories that are preexisting or belong to the user."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name 
            FROM categories 
            WHERE user_id IS NULL OR user_id = ?
            """,
            (self.user_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return rows  # e.g. [(1, 'food'), (2, 'housing'), ...]

    ###########################################################################
    # NEW METHOD: get_category_name() looks up the category's name by its ID. #
    ###########################################################################
    def get_category_name(self, category_id: int) -> str:
        """Given a category ID, return its name, or raise a ValueError if not found."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT name
                FROM categories
                WHERE id = ? AND (user_id IS NULL OR user_id = ?)
                """,
                (category_id, self.user_id)
            )
            row = cur.fetchone()
            
            if row:
                return row[0]
            else:
                raise ValueError(f"No category found with ID {category_id}")
        finally:
            conn.close()

    def save_to_db(self, spent: Spent):
        """Inserts a new expense record."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (user_id, date, amount, category) VALUES (?, ?, ?, ?)",
            (self.user_id, spent.date, spent.amount, spent.category)
        )
        conn.commit()
        conn.close()

    def fetch_all_expenses(self):
        """Returns all expenses for the user, ordered by date DESC."""
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC",
            (self.user_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def fetch_months(self, month: int):
        """Returns expenses for the given month (1-12)."""
        if not 1 <= month <= 12:
            raise ValueError("Month should be from 1 to 12.")

        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            month_str = f"{month:02d}"
            cur.execute(
                """
                SELECT * FROM expenses
                WHERE user_id = ? AND strftime('%m', date) = ?;
                """,
                (self.user_id, month_str)
            )
            rows = cur.fetchall()
            return rows
        except sqlite3.Error as e:
            print(f"Error fetching expenses for the month {month}: {e}")
            return []
        finally:
            conn.close()
