from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import database_connection, init_database
from models import Order, OrderCreate, OrderSummary, OrderUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield


app = FastAPI(title="Order Manager API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_order(row) -> dict:
    data = dict(row)
    data["total"] = round(data["quantity"] * data["unit_price"], 2)
    return data


@app.get("/api/orders", response_model=list[Order])
def list_orders():
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM orders ORDER BY datetime(created_at) DESC, id DESC"
        ).fetchall()
    return [serialize_order(row) for row in rows]


@app.get("/api/orders/summary", response_model=OrderSummary)
def get_summary():
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(SUM(quantity * unit_price), 0) AS total_revenue,
                SUM(CASE WHEN status = 'Hoàn thành' THEN 1 ELSE 0 END) AS completed_orders,
                SUM(CASE WHEN status = 'Đang xử lý' THEN 1 ELSE 0 END) AS processing_orders
            FROM orders
            """
        ).fetchone()
    return {
        "total_orders": row["total_orders"],
        "total_revenue": round(row["total_revenue"], 2),
        "completed_orders": row["completed_orders"] or 0,
        "processing_orders": row["processing_orders"] or 0,
    }


@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    with database_connection() as connection:
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return serialize_order(row)


@app.post("/api/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate):
    payload = order.model_dump()
    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO orders (customer_name, product_name, quantity, unit_price, status, note)
            VALUES (:customer_name, :product_name, :quantity, :unit_price, :status, :note)
            """,
            payload,
        )
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return serialize_order(row)


@app.put("/api/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order: OrderUpdate):
    payload = order.model_dump()
    payload["id"] = order_id
    with database_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders SET
                customer_name = :customer_name,
                product_name = :product_name,
                quantity = :quantity,
                unit_price = :unit_price,
                status = :status,
                note = :note,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """,
            payload,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return serialize_order(row)


@app.delete("/api/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int):
    with database_connection() as connection:
        cursor = connection.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
# Khai báo cuối cùng để các route /api luôn được ưu tiên trước file tĩnh.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
