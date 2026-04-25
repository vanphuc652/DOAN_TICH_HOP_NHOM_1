from fastapi import FastAPI
import pymysql
import psycopg2
import time

app = FastAPI()

def connect_mysql():
    while True:
        try:
            return pymysql.connect(
                host="mysql-db",
                user="root",
                password="root",
                database="webstore",
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception:
            print("Waiting for MySQL...")
            time.sleep(3)

def connect_postgres():
    while True:
        try:
            return psycopg2.connect(
                host="postgres",
                user="postgres",
                password="123",
                dbname="finance"
            )
        except Exception:
            print("Waiting for Postgres...")
            time.sleep(3)

@app.get("/api/report")
def get_report(page: int = 1, limit: int = 50):
    offset = (page - 1) * limit
    
    # 1. Lấy dữ liệu từ MySQL
    db_mysql = connect_mysql()
    cursor_mysql = db_mysql.cursor()
    cursor_mysql.execute(f"SELECT id, customer_id, total_amount FROM orders LIMIT {limit} OFFSET {offset}")
    orders = cursor_mysql.fetchall()
    db_mysql.close()

    if not orders:
        return {"data": [], "message": "No orders found"}

    # 2. Lấy dữ liệu từ Postgres
    db_pg = connect_postgres()
    cursor_pg = db_pg.cursor()
    order_ids = tuple([o['id'] for o in orders])
    
    # LƯU Ý DÒNG NÀY: Phải thẳng hàng với dòng trên
    query_pg = "SELECT order_id, payment_status FROM payments WHERE order_id IN %s"
    cursor_pg.execute(query_pg, (order_ids,))
    payments = cursor_pg.fetchall()
    db_pg.close()

    # 3. Khâu nối dữ liệu (Stitching)
    payment_map = {p[0]: p[1] for p in payments}
    for order in orders:
        order['payment_status'] = payment_map.get(order['id'], "PENDING")

    return {"page": page, "data": orders}