from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from auth import Auth
from management import Money, Spent

# Initialize Flask app and configure template/static folders
app = Flask(
    __name__,
    template_folder="../templates",  # Templates folder path
    static_folder="../static"  # Static folder path
)
app.secret_key = "your_secret_key_here"  # Add a secret key for sessions

# Initialize Auth
auth = Auth()

# Route to render the index page
@app.route("/")
def index():
    return render_template("index.html")

# Route to render the signup page
@app.route("/signup")
def signup_page():
    return render_template("signup.html")

# Route to handle the signup logic
@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    name = data.get("name")
    username = data.get("username")
    password = data.get("password")

    if not name or not username or not password:
        return jsonify({"success": False, "message": "All fields are required."})

    message = auth.register_user(name, username, password)
    if "successfully" in message:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "message": message})

# Route to render the login page
@app.route("/login")
def login_page():
    return render_template("login.html")

# Route to handle login logic
@app.route("/login", methods=["POST"])
def login_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "All fields are required."})

    result = auth.login_user(username, password)
    if isinstance(result, int):  # Successful login returns a user ID
        session["username"] = username
        session["user_id"] = result
        return jsonify({"success": True, "message": "Login successful", "redirect": url_for('dashboard')})
    return jsonify({"success": False, "message": result})

# Route to render the dashboard page
@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    money = Money(user_id)
    transactions = money.fetch_all_expenses()

    # Total spending (accessing the amount by index)
    amount_spent = sum([transaction[3] for transaction in transactions])

    # Fetch income
    income = money.fetch_income()

    # Calculate savings
    savings = income - amount_spent

    # Build category totals as a dictionary for Jinja2 compatibility
    category_totals = {}
    for transaction in transactions:
        category = transaction[4]  # Assuming 4th column is category
        category_totals[category] = category_totals.get(category, 0) + transaction[3]

    # Pass data to the dashboard template
    return render_template(
        "dashboard.html",
        user_name=session.get("username"),
        categories=category_totals,  # This is now a dictionary
        amount_spent=amount_spent,
        income=income,
        savings=savings,
        transactions=transactions  # Pass transactions for deletion
    )

# Route to handle fetching all categories
@app.route("/get_categories", methods=["GET"])
def get_categories():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    money = Money(user_id)
    categories = money.fetch_categories()
    return jsonify(categories=categories)

# Route to handle adding a new category
@app.route("/add_category", methods=["POST"])
def add_category():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    category_name = request.form.get("category_name")
    if not category_name:
        return jsonify({"success": False, "message": "Category name is required."})

    money = Money(user_id)
    try:
        money.add_custom_category(category_name)
        return jsonify({"success": True, "message": f"Category '{category_name}' added successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Route to handle deleting a category
@app.route("/delete_category", methods=["POST"])
def delete_category():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    category_name = request.form.get("category_name")
    if not category_name:
        return jsonify({"success": False, "message": "Category name is required."})

    money = Money(user_id)
    try:
        money.delete_category(category_name)
        return jsonify({"success": True, "message": f"Category '{category_name}' deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Route to handle adding a transaction
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    category = request.form.get("category")
    amount = request.form.get("amount")

    if not category or not amount or float(amount) <= 0:
        return jsonify({"success": False, "message": "All fields are required and amount must be positive."})

    money = Money(user_id)

    try:
        spent = Spent(float(amount), category, money)
        money.save_to_db(spent)
        return redirect(url_for("dashboard"))
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)})

# Route to handle deleting a transaction
@app.route("/delete_transaction", methods=["POST"])
def delete_transaction():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    transaction_id = request.form.get("transaction_id")
    if not transaction_id:
        return jsonify({"success": False, "message": "Transaction ID is required."})

    money = Money(user_id)
    try:
        money.delete_transaction(int(transaction_id))
        return jsonify({"success": True, "message": f"Transaction {transaction_id} was deleted."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# Route to handle updating income
@app.route("/update_income", methods=["POST"])
def update_income():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    income = request.form.get("income")
    if not income or float(income) <= 0:
        return jsonify({"success": False, "message": "Income must be a positive value."})

    money = Money(user_id)
    try:
        money.update_income(float(income))
        return jsonify({"success": True, "message": "Income updated successfully!"})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)})

# Route to handle logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
