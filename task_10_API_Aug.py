# inmem_app.py
# In-memory FastAPI CRUD for Products and Orders
# - No DB: data stored in Python dicts
# - Concurrency guarded with a threading.Lock
# - Basic validation and clear error responses

import threading
from datetime import datetime
from enum import Enum
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# App
app = FastAPI(
    title="In-Memory Shop API",
    version="0.1.0",
    description="CRUD for Products and Orders using in-memory stores",
)

# In-memory stores and counters
_lock = threading.Lock()
_products_by_id: dict[int, dict] = {}
_sku_to_id: dict[str, int] = {}
_orders_by_id: dict[int, dict] = {}

_next_product_id = 1
_next_order_id = 1

# Domain enums
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"

# Pydantic models (requests/responses)
class ProductCreate(BaseModel):
    sku: str
    name: str
    price: float
    stock: int

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

class ProductRead(BaseModel):
    id: int
    sku: str
    name: str
    price: float
    stock: int

class OrderCreate(BaseModel):
    product_id: int
    quantity: int

class OrderUpdate(BaseModel):
    quantity: Optional[int] = None
    status: Optional[OrderStatus] = None

class OrderRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime

# Optional: reset helper (not used in production)
def _reset_store_for_demo():
    global _products_by_id, _sku_to_id, _orders_by_id
    global _next_product_id, _next_order_id
    with _lock:
        _products_by_id = {}
        _sku_to_id = {}
        _orders_by_id = {}
        _next_product_id = 1
        _next_order_id = 1

# Routes: Products

@app.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate):
    global _next_product_id
    with _lock:
        if payload.sku in _sku_to_id:
            raise HTTPException(status_code=409, detail="SKU already exists")
        if payload.price <= 0:
            raise HTTPException(status_code=400, detail="Price must be > 0")
        if payload.stock < 0:
            raise HTTPException(status_code=400, detail="Stock must be >= 0")

        pid = _next_product_id
        _next_product_id += 1
        prod = {
            "id": pid,
            "sku": payload.sku,
            "name": payload.name,
            "price": payload.price,
            "stock": payload.stock,
        }
        _products_by_id[pid] = prod
        _sku_to_id[payload.sku] = pid

        return ProductRead(**prod)

@app.get("/products", response_model=List[ProductRead])
def list_products():
    with _lock:
        return [ProductRead(**p) for p in _products_by_id.values()]

@app.get("/products/{product_id}", response_model=ProductRead)
def read_product(product_id: int):
    with _lock:
        prod = _products_by_id.get(product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductRead(**prod)

@app.put("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate):
    with _lock:
        prod = _products_by_id.get(product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")

        data = payload.dict(exclude_unset=True)

        if "sku" in data:
            new_sku = data["sku"]
            if new_sku != prod["sku"] and new_sku in _sku_to_id:
                raise HTTPException(status_code=409, detail="SKU already exists")
            # update SKU mapping
            del _sku_to_id[prod["sku"]]
            _sku_to_id[new_sku] = product_id
            prod["sku"] = new_sku

        if "name" in data:
            prod["name"] = data["name"]
        if "price" in data:
            if data["price"] <= 0:
                raise HTTPException(status_code=400, detail="Price must be > 0")
            prod["price"] = data["price"]
        if "stock" in data:
            if data["stock"] < 0:
                raise HTTPException(status_code=400, detail="Stock must be >= 0")
            prod["stock"] = data["stock"]

        _products_by_id[product_id] = prod
        return ProductRead(**prod)

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    with _lock:
        prod = _products_by_id.get(product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        del _products_by_id[product_id]
        del _sku_to_id[prod["sku"]]

# Routes: Orders

@app.post("/orders", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate):
    global _next_order_id
    with _lock:
        prod = _products_by_id.get(payload.product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")
        if prod["stock"] < payload.quantity:
            raise HTTPException(status_code=409, detail="Insufficient stock")

        # Deduct stock and create order
        prod["stock"] -= payload.quantity
        _products_by_id[payload.product_id] = prod

        oid = _next_order_id
        _next_order_id += 1
        order = {
            "id": oid,
            "product_id": payload.product_id,
            "quantity": payload.quantity,
            "status": OrderStatus.PENDING,
            "created_at": datetime.utcnow(),
        }
        _orders_by_id[oid] = order
        return OrderRead(**order)

@app.get("/orders/{order_id}", response_model=OrderRead)
def read_order(order_id: int):
    with _lock:
        ord = _orders_by_id.get(order_id)
        if not ord:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderRead(**ord)

@app.put("/orders/{order_id}", response_model=OrderRead)
def update_order(order_id: int, payload: OrderUpdate):
    with _lock:
        order = _orders_by_id.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if payload.quantity is not None:
            if payload.quantity <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be > 0")
            delta = payload.quantity - order["quantity"]
            prod = _products_by_id.get(order["product_id"])
            if delta > 0:
                if prod["stock"] < delta:
                    raise HTTPException(status_code=409, detail="Insufficient stock")
                prod["stock"] -= delta
            else:
                prod["stock"] += (-delta)
            _products_by_id[order["product_id"]] = prod
            order["quantity"] = payload.quantity

        if payload.status is not None:
            order["status"] = payload.status

        _orders_by_id[order_id] = order
        return OrderRead(**order)

@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int):
    with _lock:
        order = _orders_by_id.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        # Allow deletion only if PENDING; restore stock
        if order["status"] != OrderStatus.PENDING:
            raise HTTPException(status_code=409, detail="Only PENDING orders can be deleted")
        prod = _products_by_id.get(order["product_id"])
        if prod:
            prod["stock"] += order["quantity"]
            _products_by_id[order["product_id"]] = prod
        del _orders_by_id[order_id]

# Root
@app.get("/")
def root():
    return {"msg": "In-Memory Shop API. Use /docs for OpenAPI."}