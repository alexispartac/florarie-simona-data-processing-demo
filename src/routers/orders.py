from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from src.db import get_database
from src.schemas.order import Order, OrderIn

router = APIRouter()

@router.post("/orders", response_model=Order)
def create_order(order: OrderIn):
    db = get_database()
    order_dict = order.dict()
    result = db.orders.insert_one(order_dict)
    order_dict["_id"] = str(result.inserted_id)
    return order_dict

@router.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: str):
    db = get_database()
    order = db.orders.find_one({"_id": ObjectId(order_id)})
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order["_id"] = str(order["_id"])
    return order

@router.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: str, order: OrderIn):
    db = get_database()
    result = db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": order.dict()})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found or no changes made")
    return read_order(order_id)

@router.delete("/orders/{order_id}")
def delete_order(order_id: str):
    db = get_database()
    result = db.orders.delete_one({"_id": ObjectId(order_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"detail": "Order deleted successfully"}