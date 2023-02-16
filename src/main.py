from flask import Flask, render_template, request, make_response, g, redirect, url_for
from dotenv import load_dotenv
import os
import mysql.connector

# Import logger object and set it up to log to stdout and a file
from logger import logger
from db_abstraction import DB

log = logger(logger.STDOUT | logger.FILE)


# This method should be used in the future if we split into multiple python files
# In that case we can just do `from main import l; l().log("text")`
def get_logger():
    return log


from item import Item

app = Flask(__name__)


@app.before_request
def init():
    g.db = DB()


@app.teardown_appcontext
def close_db(exception):
    g.db.close()


@app.route("/")
def index():
    sort_by = request.args.get("sortby")

    fetched_products = g.db.get_products(sort_by)

    items = [Item(product) for product in fetched_products]

    fetched_tags = g.db.get_tags()

    tags = [{"name": name, "href": f"/?sortby={name}"} for (_, name) in fetched_tags]

    return render_template(
        "index.html",
        items=items,
        tags=tags,
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
        print("oo")
        return render_template("login.html")

    username = request.form["uname"]
    print(username)
    password = request.form["psw"]
    print(password)

    # Check if password and username is in the users table.
    result = g.db.is_username_password(username, password)

    # The query returned results and, therefore, user(s)
    if len(result) > 0:
        # Extract relevant information from the DB response
        uid: str = result[0][0]
        username: str = result[0][1]
        user_type: str = result[0][5]

        # TODO: Add as proper logging later

        log.log(f"{username} ({uid}) logged in as {user_type}")

        # Redirect based on user type
        if user_type == "admin":
            log.log("redirecting to admin.html")
            res = make_response(redirect(url_for("admin")))
        else:
            log.log("redirecting to index.html")
            res = make_response(redirect(url_for("index")))

        res.set_cookie("verification", str(uid))
        return res

    else:
        # TODO: Maybe a fail2ban system in the future.

        # Invalid login! Return a error and log the event.
        log.log(f"Someone tried to log in as {username} with password {password}")
        return render_template("login.html", error="Account not found!")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/terms_of_service")
def terms_of_service():
    return render_template("terms_of_service.html")


if __name__ == "__main__":
    app.run(debug=True)
