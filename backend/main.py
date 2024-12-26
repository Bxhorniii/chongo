from auth import Auth, User
from management import Money, Spent

# Authenticate user
auth = Auth()
auth.register_user("Jozef", 'Naibaho', 'Chango123')
user_id = auth.login_user("Naibaho", "Chango123")
print(user_id)
if user_id:
    print(f"Login successful for user_id: {user_id}")

    # Create a Money instance for the logged-in user
    money = Money(user_id)

    # Save a spending
    spent = Spent(50, 'food')
    money.save_to_db(spent)

    # Fetch all expenses for the user
    expenses = money.fetch_all_expenses()
    print(expenses)
else:
    print("Invalid username or password")
