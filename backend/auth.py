import sqlite3
import hashlib

class User:
    def __init__(self, name:str, username: str, password: str, is_hashed: bool = False):
        self.name = name
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

        #DB will include id,name, username and password
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

    def register_user(self, name:str, username: str, password: str):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()

        try:
            user = User(name, username, password)
            cur.execute("INSERT INTO users (name, username, password) VALUES (?, ?, ?)",
                        (user.name, user.username, user.password))
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
            #hash the password to compare
            hashed_input = hashlib.sha256(password.encode()).hexdigest()
            if stored_password == hashed_input:
                return "Login successful!"
        return "Invalid username or password"




#test
auth = Auth()

print(auth.register_user("Matthew", "Naibaho", "Chango123"))

#right and wrong password
print(auth.login_user("Naibaho", 'Chango123'))

print(auth.login_user("Naibaho", "Callatecabron"))

#trying to register with an already existing username(should fail)
print(auth.register_user("Bjorn", "Naibaho", "password"))

