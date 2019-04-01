import os
import csv

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required

# postgres://tdvcbkhzabsenu:6264489a131e5565da3517bd12b5f7c2eeff8d5631efebfc66b65ebb1fde6d11@ec2-54-247-70-127.eu-west-1.compute.amazonaws.com:5432/d8tst0p3a5jflm
# ciGC4lMaLH8yZ2DyCAgKw
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "must provide username"
            return render_template("error.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("must provide password"):
            error = "must provide username"
            return render_template("error.html", error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("error.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/")
def logout():

    """Logout user"""

    # Foget user
    session.clear()

    # Redirect user to login page
    return redirect("/")


@app.route("/register", methods=['POST', 'GET'])
def registeration():
    if request.method == 'POST':

        """Regiseter user"""

        # Ensure that user has provided correct data
        if not request.form.get("username"):
            error = "You have provided uncorrect unsername"
            return render_template("error.html", error=error)

        # Ensure that passwords are the same
        elif request.form.get("password") == request.form.get("confirm_password"):
            error = "Your password don't identical"
            return render_template("error.html", error=error)

        username = request.form.get("username")
        # Check if username is uniqe in the database
        result = db.execute("SELECT * FROM users WHERE user_name = :user_name", {"user_name": username})

        if len(result) == 1:
            error = "Username is occupaid"
            return render_template("error.html", error=error)

        # Add to the database login and hashed password
        else:

            db.execute("INSER INTO users (username, hash) VALUES (:username, :hash)",
                {"username": request.form.get("username"), "hash": hash(request.form.get("password"))})

            rows = db.execute("SELECT * FROM users WHERE user_name = :username",
                {"username":username})

            # Remember which user has logged in
            session["user_id"] = rows[0][1]

            return render_template("index.html")

    else:
        return render_template("register.html")
