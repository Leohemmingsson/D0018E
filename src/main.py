from flask import Flask, render_template, request, make_response


app = Flask(__name__)


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
        return render_template("login.html", error="jdafg")

    elif request.method == "POST":
        username = request.form["uname"]
        password = request.form["psw"]

        print(f"Tried to login as: {username} with password {password}")

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
