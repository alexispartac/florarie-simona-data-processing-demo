from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class OrderProductProps(BaseModel):
    id: str
    title: str
    price: float
    category: str
    quantity: int

    class Config:
        orm_mode = True


class OrderProps(BaseModel):
    id: str
    userId: str
    orderNumber: int
    clientName: str
    clientEmail: str
    clientPhone: str
    clientAddress: str
    orderDate: datetime
    deliveryDate: Optional[datetime] = None
    info: Optional[str] = None
    status: Literal["Pending", "Processing", "Delivered", "Cancelled"]
    totalPrice: float
    paymentMethod: Literal["ramburs", "card"]
    products: List[OrderProductProps]

    class Config:
        orm_mode = True
