import os
import csv
import sqlite3
from datetime import datetime



class Spent:
    def __init__(self, amount: float, category: str):
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        
        self.amount = amount
        self.category = category
        self.date = datetime.now().strftime('%Y-%m-%d')

    def dic(self):
        return {'date': self.date, 'amount': f'${self.amount}', 'category': self.category}


class Money:
    def __init__(self, user_id: int):
        self.db_name = 'expenses.db'
        self.user_id = user_id

    # def filename(self):
    #     current_year = datetime.now().strftime('%Y')
    #     current_month = datetime.now().strftime('%m')

    #     return f'expenses_{current_month}_{current_year}'

    def save_to_db(self, spent: Spent):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        #create database if it doesn't exist
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL
            )
        """)

        #insert the spent into the database
        cur.execute("INSERT INTO expenses (user_id, date, amount, category) VALUES (?, ?, ?, ?)",
                    (self.user_id, spent.date, spent.amount, spent.category))
        
        conn.commit()
        conn.close()

    
    def fetch_all_expenses(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        cur.execute("SELECT * FROM expenses WHERE user_id = ?", (self.user_id,))
        rows = cur.fetchall()
        conn.close()
        return rows
    


# # Create instances
# money = Money()
# spent = Spent(50, 'food')

# # Save a spending
# money.save_to_db(spent)

# # Fetch all expenses
# expenses = money.fetch_all_expenses()
# print(expenses)
