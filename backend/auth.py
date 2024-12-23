import sqlite3
import hashlib

class User:
    def __init__(self, username: str, password: str, is_hashed: bool = False):
        self.username = username
        self.password = password if is_hashed else self.hashed_password(password)

    def hashed_password(self, password: str):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, input_password: str):
        return self.password == self.hashed_password(input_password)


class Auth:
    def __init__(self,db_name="users.db"):
        self.db_name = db_name
        self.initialize_db()

    def initialize_db(self):
        #connection to the database file
        conn = sqlite3.connect(self.db_name)

        #database cursor bjorn
        cur = conn.cursor()

        #DB will include id, username and password
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """
        )
        conn.commit()
        conn.close()

    def register_user(self, username: str, password: str):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        try:
            user = User(username, password)
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                        (user.username, user.password))
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
            user = User(username, stored_password, is_hashed=True)
            if user.verify_password(password):
                return "Login successful!"
        return "Invalid username or password"




#test
auth = Auth()

print(auth.register_user("Naibaho", "Chango123"))

#right and wrong password
print(auth.login_user("Naibaho", 'Chango123'))

print(auth.login_user("Naibaho", "Callatecabron"))

#trying to register with an already existing username(should fail)
print(auth.register_user("Naibaho", "password"))
