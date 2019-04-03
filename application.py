import os
import csv
import requests

from flask import Flask, flash, session, render_template, request, redirect, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


# postgres://tdvcbkhzabsenu:6264489a131e5565da3517bd12b5f7c2eeff8d5631efebfc66b65ebb1fde6d11@ec2-54-247-70-127.eu-west-1.compute.amazonaws.com:5432/d8tst0p3a5jflm
# ciGC4lMaLH8yZ2DyCAgKw
# https://github.com/marcorichetta/cs50w-project1/blob/master/application.py
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
    if request.method == 'POST':

        # Ensure username was submitted
        if not request.form.get("username"):

            # print(f"Here is your request: {request.form.get("username")})
            error = "must provide username"
            return render_template("error.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "must provide password"
            return render_template("error.html", error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}
                          ).fetchone()

        # Ensure username exists and password is correct
        if rows == None or not check_password_hash(rows["hash"], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("error.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
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
            error = "You have provided no unsername"
            return render_template("error.html", error=error)

        # Ensure that passwords are the same
        elif not request.form.get("password") == request.form.get("confirm_password"):
            error = "Your passwords don't identical"
            return render_template("error.html", error=error)

        # Check if username is uniqe in the database
        result = db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": request.form.get("username")}).fetchone()

        if result != None:
            error = "Username is occupaid"
            return render_template("error.html", error=error)

        # Add to the database login and hashed password
        else:

            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                {"username": request.form.get("username"), "hash": generate_password_hash(request.form.get("password"))})
            db.commit()

            lg = request.form.get("username")
            hasha = request.form.get("password")

            print("This login: {0} and hash: {1}".format(lg, hasha))

            rows = db.execute("SELECT * FROM users WHERE username = :username",
                {"username": request.form.get("username")}).fetchone()
            # Remember which user has logged in
            session["user_id"] = rows[0]

            return render_template("index.html")

    else:
        return render_template("register.html")


@login_required
@app.route("/search", methods=["GET"])
def search():

    # Ensure that user provide a data
    if not request.args.get("search"):
        error = "You don't provide anything"
        return render_template("error.html", error=error)


    # Complete search
    else:

        query = "%" + request.args.get("search") + "%"

        # Search in database
        rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
        isbn LIKE :query OR\
        title LIKE :query OR\
        author LIKE :query LIMIT 15",
        {
        "query": query
        })

        # In case of no matched books
        if rows.rowcount == 0:
            error = "No book was found"
            return render_template("error.html", error=error)

        else:

            # Return all books whitch match
            books = rows.fetchall()
            return render_template("search.html", books=books)


@login_required
@app.route("/book/<isbn>", methods=["GET", "POST"])
def book(isbn):

    if request.method == "POST":

        user = session["user_id"]

        # Ensure that user provide any opinion and rate a book
        if not request.form.get("opinion") or not request.form.get("score"):
            error = "You haven't left any opinion and/or rate this book"
            return render_template("error.html", error=error)

        # Ensure that user has no previous comments
        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND isbn_id = :isbn_id",
                                                                    {
                                                                    "user_id": user,
                                                                    "isbn_id": isbn
                                                                    })

        if row2.rowcount == 1:
            flash('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)

        # Send user score and opinion to the database
        else:

            score = request.form.get("score")
            opinion = request.form.get("opinion")

            db.execute("INSERT INTO reviews (score, opinion, user_id, isbn_id) VALUES (:score, :opinion, :user_id, :isbn_id)",
                                                                                        {
                                                                                        "score": score,
                                                                                        "opinion": opinion,
                                                                                        "user_id": session["user_id"],
                                                                                        "isbn_id": isbn
                                                                                        })
            db.commit()

            reviews = db.execute("SELECT opinion, score FROM reviews WHERE isbn_id = :isbn_id",
                                                                            {
                                                                            "isbn_id": isbn
                                                                            }).fetchall()

            book = db.execute("SELECT isbn, title, year, author FROM books WHERE isbn = :isbn",
                                                                                {
                                                                                "isbn": isbn
                                                                                }).fetchone()

            return render_template("book.html", book=book, reviews=reviews)

    # Open book by click
    else:

        book = db.execute("SELECT isbn, title, year, author FROM books WHERE isbn = :isbn",
                        {
                        "isbn": isbn
                        }).fetchone()

        # Make a request to the server
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "ciGC4lMaLH8yZ2DyCAgKw", "isbns": "{0}".format(isbn)})
        res = res.json()
        rating = res['books'][0]['average_rating']

        reviews = db.execute("SELECT opinion, score FROM reviews WHERE isbn_id = :isbn_id",
                                                                        {
                                                                        "isbn_id": isbn
                                                                        }).fetchall()

        return render_template("book.html", book=book, reviews=reviews, rating=rating)

@app.route("/api/<isbn>", methods=["GET"])
@login_required
def api_respond(isbn):

    try:
        row = db.execute("SELECT title, year, author, isbn FROM books WHERE isbn = :isbn",
                                                                            {
                                                                            "isbn": isbn
                                                                            }).fetchone()

        result = dict(row.items())
        return jsonify(result)
    except:
        abort(404)
        print("it was aborted")
