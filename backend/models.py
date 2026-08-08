from typing import Literal

from pydantic import BaseModel, Field, field_validator


OrderStatus = Literal["Mới", "Đang xử lý", "Hoàn thành"]


class OrderBase(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    product_name: str = Field(min_length=1, max_length=160)
    quantity: int = Field(gt=0, le=1_000_000)
    unit_price: float = Field(ge=0, le=1_000_000_000_000)
    status: OrderStatus = "Mới"
    note: str = Field(default="", max_length=1000)

    @field_validator("customer_name", "product_name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Không được để trống")
        return value

    @field_validator("note")
    @classmethod
    def strip_note(cls, value: str) -> str:
        return value.strip()


class OrderCreate(OrderBase):
    pass


class OrderUpdate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    total: float
    created_at: str
    updated_at: str


class OrderSummary(BaseModel):
    total_orders: int
    total_revenue: float
    completed_orders: int
    processing_orders: int

