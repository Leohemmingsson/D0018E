from flask import Flask, render_template, request, make_response, g, redirect, url_for
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
import mysql.connector
from item import Item
from review import Review
import jsonschema
from jsonschema.exceptions import ValidationError
from schemas import user_schema

# Import logger object and set it up to log to stdout and a file
from logger import logger
from db_abstraction import DB

log = logger(logger.STDOUT | logger.FILE)


# This method should be used in the future if we split into multiple python files
# In that case we can just do `from main import l; l().log("text")`
def get_logger():
    return log


app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.before_request
def init():
    g.db = DB()


@app.teardown_appcontext
def close_db(exception):
    g.db.close()


@app.route("/")
@cross_origin()
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
@cross_origin()
def admin():
    # Only give access to this page if the cookie matches a admin
    verification_cookie: str = request.cookies.get("verification")

    print(
        f"is_admin: {g.db.is_admin(verification_cookie)}, cookie: {verification_cookie}"
    )
    if not g.db.is_admin(verification_cookie):
        return "403: Forbidden"

    users = g.db.get_users()

    return render_template("admin.html", users=enumerate(users))


# Route for the admins to interact with the users.
# Requires a valid admin id in cookies.
# POST to add a user, PATCH to update a users permissions, DELETE to delete.
@app.route("/admin/users", methods=["POST", "PATCH", "DELETE"])
@cross_origin()
def admin_users():
    req_cookies = request.cookies.get("verification")
    if not g.db.is_admin(req_cookies):
        return "403: Forbidden"

    if request.method == "POST":
        json = request.get_json(force=True)

        try:
            jsonschema.validate(instance=json, schema=user_schema)
            user_json = json
        except ValidationError:
            return "Invalid json!"

        g.db.create_customer(user_json)

    if request.method == "PATCH":
        # Promote a user to admin
        info = request.get_json(force=True)

        if info["id"] and info["type"]:
            g.db.set_user_type(info["id"], info["type"])
            print(f"Set user with id {info['id']} to {info['type']}")

    if request.method == "DELETE":
        # Delete a user
        json = request.get_json(force=True)
        if json["id"]:
            print(f"Trying to delete user with id {json['id']}")
            g.db.delete_user_by_id(json["id"])

    return "200"


@app.route(
    "/admin/items",
    methods=[
        "GET",
        "POST",
        "DELETE",
        "PATCH"
    ],
)
def items():
    if request.method == "GET":
        items = g.db.get_products()
        items = [Item(product) for product in items]

        return render_template("admin_item.html", items=items)

    if request.method == "POST":
        if (
            request.form["description"]
            and request.form["name"]
            and request.form["quantity"]
            and request.form["price"]
            and request.form["image"]
        ):
            g.db.add_product(
                request.form["description"],
                request.form["name"],
                request.form["quantity"],
                request.form["price"],
                request.form["image"],
            )

            # Give a api friendly response.
            return "200"

    if request.method == "DELETE":
        id = request.get_json(force=True)["id"]

        # None check
        if id:
            g.db.remove_product(id)

            return "200"

    if request.method == "PATCH":
        pass


@app.route("/login", methods=["GET", "POST"])
@cross_origin()
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username: str = request.form["uname"]
        password: str = request.form["psw"]

        # Check if password and username is in the users table.
        result = g.db.is_username_password(username, password)

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
            log.log(f"Someone tried to log in as {username} with password {password}")
            return render_template("login.html", error="Account not found!")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        if request.form["password"] == request.form["password2"]:
            g.db.create_customer(request.form)
            return "200"


@app.route("/terms_of_service")
def terms_of_service():
    return render_template("terms_of_service.html")


@app.route("/product/<int:product_number>", methods=["GET", "POST"])
def item_page(product_number):
    if request.method == "POST":
        review_score = request.form["review_score"]
        review_text = request.form["review_text"]
        review = Review(
            [
                None,
                request.cookies.get("verification"),
                product_number,
                review_score,
                review_text,
            ]
        )
        g.db.create_review(review)

    if g.db.is_product(product_number):
        item = Item(g.db.get_product_by_id(product_number), g.db)
        fetched_reviews = g.db.get_reviews_for_product(product_number)
        reviews = [Review(review, g.db) for review in fetched_reviews]
        is_review = g.db.is_review(request.cookies.get("verification"), product_number)
        return render_template(
            "item_page.html", item=item, reviews=reviews, is_review=is_review
        )
    return "404: Not found"


if __name__ == "__main__":
    app.run(debug=True)
