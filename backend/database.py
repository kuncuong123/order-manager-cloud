import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    func,
)


SQLITE_PATH = Path(__file__).resolve().parent / "orders.db"


def get_database_url() -> str:
    """Return Render's PostgreSQL URL, or a local SQLite URL."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return f"sqlite:///{SQLITE_PATH.as_posix()}"

    # Render can expose either spelling. Selecting the driver explicitly keeps
    # SQLAlchemy from looking for psycopg2 when psycopg 3 is installed.
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


DATABASE_URL = get_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    pool_pre_ping=not IS_SQLITE,
)

metadata = MetaData()

orders = Table(
    "orders",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("customer_name", Text, nullable=False),
    Column("product_name", Text, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Float, nullable=False),
    Column("status", Text, nullable=False, server_default="Mới"),
    Column("note", Text, nullable=False, server_default=""),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
    Column("updated_at", DateTime, nullable=False, server_default=func.now()),
    CheckConstraint("quantity > 0", name="ck_orders_quantity_positive"),
    CheckConstraint("unit_price >= 0", name="ck_orders_unit_price_nonnegative"),
    CheckConstraint(
        "status IN ('Mới', 'Đang xử lý', 'Hoàn thành')",
        name="ck_orders_valid_status",
    ),
)


@contextmanager
def database_connection():
    """Open a transaction that commits on success and rolls back on error."""
    with engine.begin() as connection:
        yield connection


def init_database() -> None:
    metadata.create_all(engine)
