import sqlite3
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = "postgresql+psycopg2://example_user:password@postgres:5432/example"
parsed_url = urlparse(DATABASE_URL)

sqlite_conn = sqlite3.connect('test.db')
sqlite_cursor = sqlite_conn.cursor()

pg_conn = psycopg2.connect(
    dbname=parsed_url.path[1:],
    user=parsed_url.username,
    password=parsed_url.password,
    host=parsed_url.hostname,
    port=parsed_url.port
)
pg_cursor = pg_conn.cursor()

pg_cursor.execute("DELETE FROM orders")
pg_cursor.execute("DELETE FROM products")
pg_cursor.execute("DELETE FROM users")
pg_conn.commit()

sqlite_cursor.execute("SELECT * FROM users")
users = sqlite_cursor.fetchall()

for user in users:
    pg_cursor.execute(
        "INSERT INTO users (id, name, age, password, token, role) VALUES (%s, %s, %s, %s, %s, %s)",
        user
    )

pg_conn.commit()

sqlite_cursor.execute("SELECT * FROM products")
products = sqlite_cursor.fetchall()

for product in products:
    pg_cursor.execute(
        "INSERT INTO products (id, name, price) VALUES (%s, %s, %s)",
        product
    )

pg_conn.commit()

sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("Done")
