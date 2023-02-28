import mysql.connector
from dotenv import load_dotenv
import os


class DB:
    def __init__(self) -> None:
        load_dotenv()
        IP = os.getenv("SERVER_IP")
        DB_PASS = os.getenv("DB_PASS")
        DATABASE = os.getenv("DATABASE")

        self.mydb = mysql.connector.connect(
            host=IP,
            user="root",
            password=DB_PASS,
            database=DATABASE,
        )
        self.cursor = self.mydb.cursor()

    def close(self):
        self.cursor.close()

    def get_products(self, sort_by: str = None):
        if sort_by == None:
            self.cursor.execute("SELECT * FROM Item")
        else:
            if type(sort_by) == str:
                sort_by = [sort_by]
            sql = f"SELECT Item.* FROM Item LEFT JOIN TagGroup ON Item.id = TagGroup.item_id WHERE TagGroup.tag_id IN (SELECT Tag.id FROM Tag WHERE Tag.value = %s)"
            self.cursor.execute(sql, sort_by)

        fetched_products = self.cursor.fetchall()

        return fetched_products

    def get_product_by_id(self, product_id):
        sql = "SELECT * FROM Item WHERE id = %s"
        val = (product_id,)
        self.cursor.execute(sql, val)
        fetched_products = self.cursor.fetchone()

        return fetched_products

    ### STUFF WITH TAGS ###
    def get_tags(self):
        self.cursor.execute("SELECT * FROM Tag")
        fetched_tags = self.cursor.fetchall()

        return fetched_tags

    ### STUFF WITH REVIEWS ###
    def get_reviews_for_product(self, product_id):
        sql = "SELECT * FROM Review WHERE item_id = %s"
        val = (product_id,)
        self.cursor.execute(sql, val)
        fetched_reviews = self.cursor.fetchall()
        return fetched_reviews

    def get_review_score_for_product(self, product_id):
        sql = "SELECT CAST(AVG(score) AS DECIMAL(2, 1)) FROM Review WHERE item_id = %s"
        val = (product_id,)

        self.cursor.execute(sql, val)
        fetched_score = self.cursor.fetchone()
        return fetched_score

    def is_review(self, user_id, product_id):
        sql = "SELECT * FROM Review WHERE user_id = %s and item_id = %s"
        values = (user_id, product_id)
        self.cursor.execute(sql, values)
        review = self.cursor.fetchall()

        return bool(len(review))

    def create_review(self, review_info):
        sql = "INSERT INTO Review (user_id, item_id, score, comment) VALUES (%s, %s, %s, %s)"
        val = (
            review_info.user_id,
            review_info.item_id,
            review_info.rating,
            review_info.comment,
        )

        self.cursor.execute(sql, val)
        self.mydb.commit()

    def get_tags_for_product(self, product_id):
        sql = "SELECT Tag.value FROM Tag LEFT JOIN TagGroup ON Tag.id = TagGroup.tag_id WHERE TagGroup.item_id = %s"
        val = (product_id,)
        self.cursor.execute(sql, val)
        fetched_tags = self.cursor.fetchall()

        return fetched_tags

    def is_username_password(self, username, password):
        sql = "SELECT * FROM User WHERE username = %s and password = %s"
        values = (username, password)
        self.cursor.execute(sql, values)
        user = self.cursor.fetchall()

        return user

    def get_cart(self, id):
        pass

    def create_customer(self, user_info):
        sql = "INSERT INTO User (username, first_name, last_name, password, type) VALUES (%s, %s, %s, %s, %s)"
        val = (
            user_info["username"],
            user_info["first_name"],
            user_info["last_name"],
            user_info["password"],
            "customer",
        )

        self.cursor.execute(sql, val)
        self.mydb.commit()

    def set_user_type(self, user_id, new_type):
        sql = "UPDATE User SET type = %s where id = %s"
        val = (new_type, user_id)

        self.cursor.execute(sql, val)
        self.mydb.commit()

    def delete_user_by_id(self, user_id):
        sql = "DELETE FROM User WHERE id = %s"
        val = (user_id,)
        self.cursor.execute(sql, val)
        self.mydb.commit()

    def is_admin(self, cookie):
        if not cookie:
            return False

        sql = 'SELECT * FROM User WHERE id = %s and type = "admin"'
        val = (cookie,)
        self.cursor.execute(sql, val)
        return len(self.cursor.fetchall()) > 0

    def get_users(self):
        self.cursor.execute("select * from User")
        return self.cursor.fetchall()

    def get_username(self, user_id):
        sql = "SELECT username FROM User WHERE id = %s"
        val = (user_id,)
        self.cursor.execute(sql, val)
        return self.cursor.fetchone()[0]

    def is_product(self, product_id):
        sql = "SELECT * FROM Item WHERE id = %s"
        val = (product_id,)
        self.cursor.execute(sql, val)
        return len(self.cursor.fetchall()) > 0

    ### STUFF WITH CART ###

    def get_cart(self, user_id):
        cart_id = self.__get_active_cart_id(user_id)
        sql = "SELECT Item.*, ItemGroup.quantity FROM Item LEFT JOIN ItemGroup ON Item.id = ItemGroup.item_id WHERE ItemGroup.order_id = %s"
        val = (cart_id,)
        self.cursor.execute(sql, val)
        return self.cursor.fetchall()

    def add_to_cart(self, user_id, item_id):
        """
        Add a item to the cart of the user
        If item in cart, increase quantity
        """
        cart_id = self.__get_active_cart_id(user_id)

        if not self.__is_item_in_cart(user_id, item_id, cart_id):
            self.__add_item_to_cart(cart_id, item_id)
            return
        self.__add_quant_cart_item(cart_id, item_id)

    def remove_from_cart(self, user_id, item_id):
        """
        Subtract one from the quantity of the item in the cart
        if only 1 left, remove item from cart
        """
        cart_id = self.__get_active_cart_id(user_id)

        if self.__quantity_in_cart(user_id, item_id)[0] > 1:
            self.__remove_one_from_item(cart_id, item_id)
            return

        sql = "DELETE FROM ItemGroup WHERE order_id = %s and item_id = %s"
        val = (cart_id, item_id)
        self.cursor.execute(sql, val)
        self.mydb.commit()

    def __quantity_in_cart(self, user_id, item_id):
        cart_id = self.__get_active_cart_id(user_id)

        sql = "SELECT quantity FROM ItemGroup WHERE order_id = %s and item_id = %s"
        val = (cart_id, item_id)
        self.cursor.execute(sql, val)
        return self.cursor.fetchone()

    def __remove_one_from_item(self, cart_id, item_id):
        sql = "UPDATE ItemGroup SET quantity = quantity - 1 WHERE order_id = %s and item_id = %s"
        val = (cart_id, item_id)
        self.cursor.execute(sql, val)
        self.mydb.commit()

    def __get_active_cart_id(self, user_id):
        if not len(self.__get_active_cart(user_id)) > 0:
            self.__create_cart(user_id)
        return self.__get_active_cart(user_id)[0][0]

    def __get_active_cart(self, user_id):
        sql = (
            "SELECT * FROM OrderHead WHERE customer_id = %s and status = 'in_progress'"
        )
        val = (user_id,)
        self.cursor.execute(sql, val)
        return self.cursor.fetchall()

    def __create_cart(self, user_id):
        sql = "INSERT INTO OrderHead (customer_id, status) VALUES (%s, 'in_progress')"
        val = (user_id,)
        self.cursor.execute(sql, val)
        self.mydb.commit()

    def __add_quant_cart_item(self, cart_id, item_id):
        sql = "UPDATE ItemGroup SET quantity = quantity + 1 WHERE order_id = %s and item_id = %s"
        val = (cart_id, item_id)

        self.cursor.execute(sql, val)
        self.mydb.commit()

    def __add_item_to_cart(self, order_id, item_id):
        sql = "INSERT INTO ItemGroup (order_id, item_id, quantity) VALUES (%s, %s, 1)"
        val = (order_id, item_id)
        self.cursor.execute(sql, val)
        self.mydb.commit()

    def __is_item_in_cart(self, user_id, item_id, order_id):
        sql = "SELECT * FROM ItemGroup WHERE order_id = %s and item_id = %s and order_id = %s"
        val = (user_id, item_id, order_id)
        self.cursor.execute(sql, val)
        return len(self.cursor.fetchall()) > 0


if __name__ == "__main__":
    db = DB()

    tags = db.get_tags_for_product(2)
    print(tags)
