import psycopg2
from pymongo import MongoClient
import os


pg_conn = psycopg2.connect(
    dbname="example",
    user="example_user",
    password="password",
    host="postgres",
    port="5432"
)
pg_cursor = pg_conn.cursor()


MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:password@mongo:27017/example_db?authSource=admin")

mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["example_db"]


mongo_db.users.delete_many({})
mongo_db.products.delete_many({})
mongo_db.orders.delete_many({})


pg_cursor.execute("SELECT * FROM users")
users = pg_cursor.fetchall()

for user in users:
    user_doc = {
        "_id": user[0],
        "name": user[1],
        "age": user[2],
        "password": user[3],
        "token": user[4],
        "role": user[5]
    }
    mongo_db.users.insert_one(user_doc)


pg_cursor.execute("SELECT * FROM products")
products = pg_cursor.fetchall()

for product in products:
    product_doc = {
        "_id": product[0],
        "name": product[1],
        "price": product[2]
    }
    mongo_db.products.insert_one(product_doc)


pg_cursor.execute("SELECT * FROM orders")
orders = pg_cursor.fetchall()

for order in orders:
    order_doc = {
        "_id": order[0],
        "user_id": order[1],
        "product_id": order[2],
        "quantity": order[3]
    }
    mongo_db.orders.insert_one(order_doc)

pg_cursor.close()
pg_conn.close()
mongo_client.close()

print("Done")
