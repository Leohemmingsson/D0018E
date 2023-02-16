import mysql.connector
from dotenv import load_dotenv
import os


def connect():
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

    return mydb


mydb = connect()
cursor = mydb.cursor()
# cursor.execute("UPDATE User SET type = 'admin' WHERE id = 2")
# mydb.commit()

cursor.execute("SELECT * FROM User")
for x in cursor.fetchall():
    print(x)


cursor.close()
