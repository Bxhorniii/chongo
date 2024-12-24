from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from backend.auth import Auth

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

    message = auth.login_user(username, password)
    if "successful" in message:
        session["username"] = username
        return jsonify({"success": True, "message": message, "redirect": url_for("dashboard")})
    return jsonify({"success": False, "message": message})


# Route to render the dashboard page
@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    if not username:
        return redirect(url_for("login_page"))

    user_name = auth.get_user_name(username)  # Assuming auth has a method to fetch the user's full name
    return render_template("dashboard.html", user_name=user_name)


# Route to handle logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
