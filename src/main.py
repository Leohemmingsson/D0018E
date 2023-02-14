from flask import Flask, render_template, request, make_response, g, redirect, url_for
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
import mysql.connector

import jsonschema
from schemas import user_schema


app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


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


def is_admin(cookie: any) -> bool:
    if not cookie:
        return False

    db = get_db()
    c = db.cursor()
    c.execute(f'SELECT * FROM User WHERE id = {cookie} and type = "admin"')
    return len(c.fetchall()) > 0


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)

    if db is not None:
        db.close()


@app.route("/")
@cross_origin()
def index():
    return render_template(
        "index.html",
        variable="oooo",
    )


@app.route("/admin", methods=["GET"])
@cross_origin()
def admin():
    # Only give access to this page if the cookie matches a admin
    verification_cookie: str = request.cookies.get("verification")

    print(f"is_admin: {is_admin(verification_cookie)}, cookie: {verification_cookie}")
    if not is_admin(verification_cookie):
        return "403: Forbidden"

    db = get_db()
    c = db.cursor()

    c.execute("select * from User")
    users = c.fetchall()

    return render_template("admin.html", users=enumerate(users))


# Route for the admins to interact with the users.
# Requires a valid admin id in cookies.
# POST to add a user, PUT to update a users permissions, DELETE to delete.
@app.route("/admin/users", methods=["POST", "PUT", "DELETE"])
@cross_origin()
def users():
    req_cookies = request.cookies.get("verification")
    # if not is_admin(req_cookies):
    # return "403: Forbidden"

    if request.method == "POST":
        json = request.get_json(force=True)

        try:
            jsonschema.validate(instance=json, schema=user_schema)
        except:
            return "Invalid json!"

        # Create a new user
        db = get_db()
        c = db.cursor()
        sql = "INSERT INTO User (username, first_name, last_name, password, type) VALUES (%s, %s, %s, %s, %s)"
        val = (
            json["username"],
            json["first_name"],
            json["last_name"],
            json["password"],
            "customer",
        )
        c.execute(sql, val)
        db.commit()

    if request.method == "PUT":
        # Promote a user to admin
        json = request.get_json(force=True)
        if json["id"] and json["type"]:
            db = get_db()
            c = db.cursor()
            c.execute(f"UPDATE User SET type = \"{json['type']}\" where id = {json['id']}")
            db.commit()


    if request.method == "DELETE":
        # Delete a user
        json = request.get_json(force=True)
        if json["id"]:
            print(f"Trying to delete user with id {json['id']}")

            db = get_db()
            c = db.cursor()
            c.execute(f"DELETE FROM User WHERE id = {json['id']}")
            db.commit()

    return "wow"


@app.route("/login", methods=["GET", "POST"])
@cross_origin()
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username: str = request.form["uname"]
        password: str = request.form["psw"]

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
