from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import case, delete, func, insert, select, update

try:
    # Package import, e.g. `uvicorn backend.main:app` from the repository root.
    from .database import database_connection, init_database, orders
    from .models import Order, OrderCreate, OrderSummary, OrderUpdate
except ImportError:
    # Script import, e.g. `uvicorn main:app` with Render Root Directory = backend.
    from database import database_connection, init_database, orders
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
    data = dict(row._mapping)
    for field in ("created_at", "updated_at"):
        if isinstance(data[field], datetime):
            data[field] = data[field].isoformat(sep=" ")
    data["total"] = round(data["quantity"] * data["unit_price"], 2)
    return data


@app.get("/api/orders", response_model=list[Order])
def list_orders():
    statement = select(orders).order_by(orders.c.created_at.desc(), orders.c.id.desc())
    with database_connection() as connection:
        rows = connection.execute(statement).fetchall()
    return [serialize_order(row) for row in rows]


@app.get("/api/orders/summary", response_model=OrderSummary)
def get_summary():
    statement = select(
        func.count().label("total_orders"),
        func.coalesce(func.sum(orders.c.quantity * orders.c.unit_price), 0).label("total_revenue"),
        func.sum(case((orders.c.status == "Hoàn thành", 1), else_=0)).label("completed_orders"),
        func.sum(case((orders.c.status == "Đang xử lý", 1), else_=0)).label("processing_orders"),
    ).select_from(orders)
    with database_connection() as connection:
        row = connection.execute(statement).one()._mapping
    return {
        "total_orders": row["total_orders"],
        "total_revenue": round(float(row["total_revenue"]), 2),
        "completed_orders": row["completed_orders"] or 0,
        "processing_orders": row["processing_orders"] or 0,
    }


@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    with database_connection() as connection:
        row = connection.execute(select(orders).where(orders.c.id == order_id)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return serialize_order(row)


@app.post("/api/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate):
    with database_connection() as connection:
        result = connection.execute(insert(orders).values(**order.model_dump()))
        order_id = result.inserted_primary_key[0]
        row = connection.execute(select(orders).where(orders.c.id == order_id)).one()
    return serialize_order(row)


@app.put("/api/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order: OrderUpdate):
    statement = (
        update(orders)
        .where(orders.c.id == order_id)
        .values(**order.model_dump(), updated_at=func.now())
    )
    with database_connection() as connection:
        result = connection.execute(statement)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
        row = connection.execute(select(orders).where(orders.c.id == order_id)).one()
    return serialize_order(row)


@app.delete("/api/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int):
    with database_connection() as connection:
        result = connection.execute(delete(orders).where(orders.c.id == order_id))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
# Mount last so /api routes always take precedence over static files.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
