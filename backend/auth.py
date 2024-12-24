import sqlite3
import bcrypt


class User:
    def __init__(self, name: str, username: str, password: str, is_hashed: bool = False):
        self.name = name
        self.username = username
        self.password = password if is_hashed else self.hash_password(password)

    @staticmethod
    def hash_password(password: str):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, input_password: str):
        return bcrypt.checkpw(input_password.encode(), self.password.encode())


class Auth:
    def __init__(self, db_name="users.db"):
        self.db_name = db_name
        self.initialize_db()

    def initialize_db(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def register_user(self, name: str, username: str, password: str):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            user = User(name, username, password)
            cur.execute(
                "INSERT INTO users (name, username, password) VALUES (?, ?, ?)",
                (user.name, user.username, user.password),
            )
            conn.commit()
            return 'User registered successfully, Welcome Chango!'
        except sqlite3.IntegrityError:
            return 'Username already exists'
        finally:
            conn.close()

    def login_user(self, username: str, password: str):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cur.fetchone()
        conn.close()

        if result:
            stored_password = result[0]
            if bcrypt.checkpw(password.encode(), stored_password.encode()):
                return "Login successful!"
        return "Invalid username or password"

    def get_user_name(self, username: str):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE username = ?", (username,))
        result = cur.fetchone()
        conn.close()
        return result[0] if result else None
