from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from auth import Auth
from management import Money, Spent

# Initialize Flask app and configure template/static folders
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)
app.secret_key = "your_secret_key_here"

# Initialize Auth
auth = Auth()


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/transaction')
def transaction():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template('transaction.html')


@app.route("/signup")
def signup_page():
    return render_template("signup.html")


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


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "All fields are required."})

    result = auth.login_user(username, password)
    if isinstance(result, int):  # Successful login returns user ID
        session["username"] = username
        session["user_id"] = result
        return jsonify({"success": True, "message": "Login successful", "redirect": url_for('dashboard')})
    return jsonify({"success": False, "message": result})


@app.route('/check_auth')
def check_auth():
    if session.get("user_id"):
        return jsonify({"authenticated": True})
    return jsonify({"authenticated": False}), 401


@app.route('/categories')
def get_categories():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    money = Money(user_id)
    categories = money.fetch_categories()
    return jsonify({
        "categories": [
            {"id": cat[0], "name": cat[1]} for cat in categories
        ]
    })


@app.route('/transactions')
def get_transactions():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    money = Money(user_id)
    transactions = money.fetch_all_expenses()
    formatted_transactions = []

    for transaction in transactions:
        formatted_transactions.append({
            "id": transaction[0],
            # If transaction[2] is a string, use it directly; otherwise strftime
            "date": transaction[2] if isinstance(transaction[2], str) else transaction[2].strftime("%Y-%m-%d"),
            "amount": float(transaction[3]),
            "category": transaction[4]
        })

    return jsonify({"transactions": formatted_transactions})


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    money = Money(user_id)
    transactions = money.fetch_all_expenses()

    # Calculate total expenses
    amount_spent = sum(transaction[3] for transaction in transactions)

    # Fetch income (budget)
    income = money.fetch_income()
    if income is None:
        income = 0

    # Calculate savings and category totals
    savings = income - amount_spent
    categories = {}
    for transaction in transactions:
        category = transaction[4]
        categories[category] = categories.get(category, 0) + transaction[3]

    # Calculate budget percentage spent
    budget_percentage_spent = (amount_spent / income * 100) if income > 0 else 0

    return render_template(
        "dashboard.html",
        user_name=session.get("username"),
        budget=income,
        expenses=amount_spent,
        categories=categories,
        budget_percentage_spent=budget_percentage_spent,
        savings=savings,
        transactions=transactions,
    )


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.json
    category_name = data.get("category_name")
    amount = data.get("amount")

    if not category_name or amount is None:
        return jsonify({"success": False, "error": "Missing required fields"})

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be positive"})

        money = Money(user_id)
        spent = Spent(amount, category_name, money)
        money.save_to_db(spent)

        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/add_category", methods=["POST"])
def add_category():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.json
    category_name = data.get("name")

    if not category_name:
        return jsonify({"success": False, "error": "Category name is required"})

    money = Money(user_id)
    try:
        money.add_custom_category(category_name)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/delete_category", methods=["POST"])
def delete_category():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    category_name = request.form.get("category_name")
    if not category_name:
        return jsonify({"success": False, "error": "Category name is required"})

    money = Money(user_id)
    try:
        money.delete_category(category_name)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/delete_transaction/<int:id>", methods=["DELETE"])
def delete_transaction(id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    money = Money(user_id)
    try:
        money.delete_transaction(id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/update_income", methods=["POST"])
def update_income():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    try:
        income = float(request.form.get("income", 0))
        if income <= 0:
            return jsonify({"success": False, "error": "Income must be positive"})

        money = Money(user_id)
        money.update_income(income)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
