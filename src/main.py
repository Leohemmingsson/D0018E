from flask import (
    Flask,
    render_template,
    request,
    make_response,
    g,
    redirect,
    url_for,
    send_from_directory,
)
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
import mysql.connector
from item import Item
from review import Review
from order import Order
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


@app.route("/", methods=["GET", "POST"])
@cross_origin()
def index():
    if request.method == "POST":
        cookie = request.cookies.get("verification")
        g.db.checkout_cart(cookie)

    sort_by = request.args.get("sortby")

    fetched_products = g.db.get_products(sort_by)

    items = [Item(product) for product in fetched_products]

    fetched_tags = g.db.get_tags()

    tags = [{"name": name, "href": f"/?sortby={name}"} for (_, name) in fetched_tags]

    verification_cookie: str = request.cookies.get("verification")
    if verification_cookie:
        products_in_basket = g.db.get_cart(verification_cookie)
        items_in_basket = [Item(product) for product in products_in_basket]
    else:
        items_in_basket = []

    return render_template(
        "index.html",
        items=items,
        tags=tags,
        items_in_basket=items_in_basket,
        user = g.db.get_username(verification_cookie)
    )


@app.route("/admin", methods=["GET"])
@cross_origin()
def admin():
    # Only give access to this page if the cookie matches a admin
    verification_cookie: str = request.cookies.get("verification")

    log.log(
        f"is_admin: {g.db.is_admin(verification_cookie)}, cookie: {verification_cookie}"
    )
    if not g.db.is_admin(verification_cookie):
        return "403: Forbidden"

    users = g.db.get_users()

    return render_template("admin_index.html", users=enumerate(users))


# Route for the admins to interact with the users.
# Requires a valid admin id in cookies.
# POST to add a user, PATCH to update a users permissions, DELETE to delete.
@app.route("/admin/users", methods=["POST", "PATCH", "DELETE", "GET"])
@cross_origin()
def admin_users():
    req_cookies = request.cookies.get("verification")
    if not g.db.is_admin(req_cookies):
        return "403: Forbidden"

    if request.method == "GET":
        users = g.db.get_users()
        return render_template("admin_users.html", users=enumerate(users))

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
            log.log(f"Set user with id {info['id']} to {info['type']}")

    if request.method == "DELETE":
        # Delete a user
        json = request.get_json(force=True)
        if json["id"]:
            log.log(f"Trying to delete user with id {json['id']}")
            g.db.delete_user_by_id(json["id"])

    return "200"


@app.route(
    "/admin/items",
    methods=["GET", "POST", "DELETE", "PATCH"],
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
        id = request.get_json(force=True)["item_id"]

        # None check
        if id:
            g.db.remove_product(id)
            log.log("Removed item with id: {id}")

            return "200"

    if request.method == "PATCH":
        item = request.get_json(force=True)

        g.db.update_product(
            item["id"],
            item["description"],
            item["name"],
            item["quantity"],
            item["price"],
            item["image"],
        )

        return "200"


@app.route("/login", methods=["GET", "POST"])
@cross_origin()
def login():
    if request.method == "GET":
        return render_template("login.html", user=g.db.get_username(request.cookies.get("verification")))

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
            return render_template("login.html", error="Account not found!", user=g.db.get_username(request.cookies.get("verification")))


# POST   add a item to the cart
# DELETE delete a item from the cart
@app.route("/cart/<int:item_id>", methods=["POST", "DELETE"])
def cart(item_id):
    if request.method == "POST":
        # The user id (verification cookie) is also the cart id.
        cart_id = request.cookies.get("verification")
        if not cart_id:
            # If there is no verification cookie then we are not logged in.
            return "You are not logged in!"

        g.db.add_to_cart(cart_id, item_id)
        log.log(f"user #{cart_id} added item #{item_id} to their cart")

    elif request.method == "DELETE":
        cart_id = request.cookies.get("verification")
        if not cart_id:
            # If there is no verification cookie then we are not logged in.
            return "You are not logged in!"

        g.db.remove_from_cart(cart_id, item_id)
        log.log(f"Removing item #{item_id} from cart #{cart_id}")

    return "200"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", user=g.db.get_username(request.cookies.get("verification")))
    elif request.method == "POST":
        if request.form["password"] == request.form["password2"]:
            g.db.create_customer(request.form)
            return "200"


@app.route("/terms_of_service")
def terms_of_service():
    return render_template("terms_of_service.html", user = g.db.get_username(request.cookies.get("verification")))


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
            "item_page.html", item=item, reviews=reviews, is_review=is_review, user = g.db.get_username(request.cookies.get("verification"))
        )
    return "404: Not found"


@app.route("/order", methods=["GET"])
def order_history():
    cookie = request.cookies.get("verification")
    fetched_orders = g.db.get_orders_for_user(cookie)
    orders = [Order(order, g.db) for order in fetched_orders]
    return render_template("order_index.html", orders=enumerate(orders))


@app.route("/order/<int:order_id>", methods=["GET"])
def one_order(order_id):
    cookie = request.cookies.get("verification")
    fetched_products = g.db.get_products_from_order(order_id, cookie)
    items = [Item(item) for item in fetched_products]
    return render_template("one_order.html", items=enumerate(items))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


if __name__ == "__main__":
    app.run(debug=True)
