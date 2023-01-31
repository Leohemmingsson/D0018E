from flask import Flask, render_template, request, make_response, g, redirect, url_for
from dotenv import load_dotenv
import os
import mysql.connector


app = Flask(__name__)


def get_db():
    if "db" not in g:
        load_dotenv()
        mydb = mysql.connector.connect(
            host=os.getenv("SERVER_IP"),
            user="root",
            password=os.getenv("DB_PASS"),
            database=os.getenv("DATABASE"),
        )

        g.db = mydb

    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)

    if db is not None:
        db.close()


@app.route("/")
def index():
    varaiable = []
    for i in range(10):
        varaiable.append(
            {
                "id": 1,
                "name": "awesome monitor",
                "price": 100,
                "quantity": 1,
                "image": "https://i.computersalg.dk/digitalcontent/360/4305/43053377.jpg",
                "description": "This is a monitor",
                "href": "/product/1",
            }
        )
    return render_template(
        "index.html",
        variable=varaiable,
    )


@app.route("/admin", methods=["GET"])
def admin():
    # Only give access to this page if the cookie matches a admin
    verification_cookie: str = request.cookies.get("verification")

    # No cookie, user definetly unauthorized.
    if not verification_cookie:
        return "Access denied!"

    # TODO: Check if the verification cookie matches any admin in the database

    return render_template("admin.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form["uname"]
        password = request.form["psw"]

        db = get_db()
        cursor = db.cursor()

        # Check if password and username is in the users table.
        cursor.execute(
            f"SELECT * FROM User WHERE username = '{username}' and password = '{password}'"
        )
        result = cursor.fetchall()

        # The query returned results and, therefore, user(s)
        if len(result) > 0:

            # Extract relevant information from the DB response
            uid: str = result[0][0]
            username: str = result[0][1]
            user_type: str = result[0][5]

            # TODO: Add as proper logging later
            print(f"{username} ({uid}) logged in as {user_type}")

            # Redirect based on user type
            if user_type == "admin":
                print("redirecting to admin.html")
                res = make_response(redirect(url_for("admin")))
            else:
                print("redirecting to index.html")
                res = make_response(redirect(url_for("index")))

            res.set_cookie("verification", str(uid))
            return res

        else:
            # TODO: Maybe a fail2ban system in the future.

            # Invalid login! Return a error and log the event.
            print(f"Someone tried to log in as {username} with password {password}")
            return render_template("login.html", error="Account not found!")


if __name__ == "__main__":
    app.run(debug=True)
