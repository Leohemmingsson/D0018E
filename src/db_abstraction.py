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
            print("Is none")
            self.cursor.execute("SELECT * FROM Item")
        else:
            if type(sort_by) == str:
                sort_by = [sort_by]
            sql = f"SELECT Item.* FROM Item LEFT JOIN TagGroup ON Item.id = TagGroup.item_id WHERE TagGroup.item_id IN (SELECT Tag.id FROM Tag WHERE Tag.value = %s)"
            self.cursor.execute(sql, sort_by)

        fetched_products = self.cursor.fetchall()

        return fetched_products

    def get_tags(self):
        self.cursor.execute("SELECT * FROM Tag")
        fetched_tags = self.cursor.fetchall()

        return fetched_tags

    def is_username_password(self, username, password):
        self.cursor.execute(
            f"SELECT * FROM User WHERE username = '{username}' and password = '{password}'"
        )
        user = self.cursor.fetchall()

        return user

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
        self.cursor.execute(
            f"UPDATE User SET type = \"{new_type}\" where id = {user_id}"
        )
        self.mydb.commit()

    def delete_user_by_id(self, user_id):
        self.cursor.execute(f"DELETE FROM User WHERE id = {json['id']}")
        self.mydb.commit()

    def is_admin(self, cookie):
        if not cookie:
            return False

        self.cursor.execute(f'SELECT * FROM User WHERE id = {cookie} and type = "admin"')
        return len(self.cursor.fetchall()) > 0

    def get_users(self):
        self.cursor.execute("select * from User")
        return self.cursor.fetchall()

    ### TODO METHODS ###
    def add_product(self, item: Item):
        # Should recieve a Item and add it to the database
        pass

    def remove_product(self, item_id):
        # Should remove the item with the specified item_id
        pass


if __name__ == "__main__":
    db = DB()

    user_info = {
        "username": "testP",
        "first_name": "Pelle",
        "last_name": "Olsson",
        "password": "Pass",
    }

    print(db.create_customer(user_info))
