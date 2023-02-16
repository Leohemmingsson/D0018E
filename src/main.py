from flask import Flask, render_template, request, make_response, g, redirect, url_for
from dotenv import load_dotenv
import os
import mysql.connector

# Import logger object and set it up to log to stdout and a file
from logger import logger

log = logger(logger.STDOUT | logger.FILE)

# This method should be used in the future if we split into multiple python files
# In that case we can just do `from main import l; l().log("text")`
def get_logger():
    return log


from item import Item

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
    sort_by = [request.args.get("sortby")]
    mydb = get_db()
    cursor = mydb.cursor()

    if sort_by[0] == None:
        cursor.execute("SELECT * FROM Item")
    else:

        sql = f"SELECT Item.* FROM Item LEFT JOIN TagGroup ON Item.id = TagGroup.item_id WHERE TagGroup.item_id IN (SELECT Tag.id FROM Tag WHERE Tag.value = %s)"
        print(sql)
        cursor.execute(sql, sort_by)
    fetched_products = cursor.fetchall()

    items = [Item(product) for product in fetched_products]

    cursor.execute("SELECT * FROM Tag")
    fetched_tags = cursor.fetchall()
    tags = []
    for one_tag in fetched_tags:
        tags.append({"name": one_tag[1], "href": f"/?sortby={one_tag[1]}"})

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

@app.route("/item_page")
def item_page():
    return render_template("item_page.html")

if __name__ == "__main__":
    app.run(debug=True)
