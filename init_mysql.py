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


def remove_table():
    mydb = connect()
    mycursor = mydb.cursor()

    mycursor.execute("DROP TABLE Review")
    mycursor.execute("DROP TABLE ItemGroup")
    mycursor.execute("DROP TABLE TagGroup")
    mycursor.execute("DROP TABLE Item")
    mycursor.execute("DROP TABLE Tag")
    mycursor.execute("DROP TABLE User")

    mydb.commit()
    mydb.close()


def init_tables():
    mydb = connect()
    mycursor = mydb.cursor()

    with open("scheme.txt", "r") as fh:
        query = ""
        for row in fh:
            if row.strip() == "" and query != "":
                print("yes")
                print(query)
                mycursor.execute(query)
                query = ""
            else:
                query += row

    mydb.commit()
    # print(var)
    mydb.close()


# remove_table()
init_tables()
