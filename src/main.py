from flask import Flask, render_template, request, make_response, g
from dotenv import load_dotenv
import os 
import mysql.connector


app = Flask(__name__)


def get_db():
    if 'db' not in g:
        load_dotenv()
        IP = os.getenv("SERVER_IP")
        DB_PASS = os.getenv("DB_PASS")
        DATABASE = os.getenv("DATABASE")

        mydb = mysql.connector.connect(
            host=IP,
            user="root",
            password=DB_PASS,
            database=DATABASE,
        )

        g.db = mydb

    return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)

    if db is not None:
        db.close()

@app.route("/")
def hello_world():
    return render_template(
        "index.html",
        variable="oooo",
    )


@app.route("/admin", methods=["GET"])
def admin():
    # Only give access to this page if the cookie matches a admin
    verification_cookie = request.cookies.get("verification")

    # No cookie, user definetly unauthorized.
    if not verification_cookie:
        return "Access denied!"

    # Check if the verification cookie matches any admin in the database

    pass


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form["uname"]
        password = request.form["psw"]

        print(f"Tried to login as: {username} with password {password}")

        db = get_db()
        c = db.cursor()

        c.execute(f"SELECT * FROM User WHERE username = \'{username}\' and password = \'{password}\'")
        result = c.fetchall()
        if len(result) > 0:
            print("Logged in!")
        else:
            print("wrong!")
        

        # Check if password and username is in the users table.
        # Redirect based on the response:
        # If the found user is a normal user, redirect to index.html with a logged in cookie
        # res = make_response(render_template("index.html"))
        # res.set_cookie("verification", user_id_from_sql_query)
        # if the user is a admin, redirect to admin_page.html with a logged in cookie
        # if none, redirect to login.html with a error
        #
        # The logged in cookie's content should be the users id. This is insecure but easily changeable
        # and shouldnt matter too much since its just a demo.

        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
