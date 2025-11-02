from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Order(BaseModel):
    order_id: str
    customer_name: str
    product_name: str
    quantity: int
    order_date: datetime
    status: Optional[str] = "Pending"  # Default status is 'Pending'