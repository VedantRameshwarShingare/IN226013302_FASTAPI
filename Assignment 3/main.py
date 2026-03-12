from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()


products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True}
]

feedback = []
orders = []


class Product(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str
    in_stock: bool


class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]


class Order(BaseModel):
    product_id: int
    quantity: int




@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):

    filtered = [p for p in products if p["category"].lower() == category_name.lower()]

    if not filtered:
        return {"error": "No products found in this category"}

    return {"products": filtered, "count": len(filtered)}


@app.get("/products/instock")
def instock_products():

    instock = [p for p in products if p["in_stock"]]

    return {"in_stock_products": instock, "count": len(instock)}


@app.get("/store/summary")
def store_summary():

    total = len(products)
    instock = len([p for p in products if p["in_stock"]])
    outstock = total - instock
    categories = list(set([p["category"] for p in products]))

    return {
        "store_name": "My E-commerce Store",
        "total_products": total,
        "in_stock": instock,
        "out_of_stock": outstock,
        "categories": categories
    }


@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    matched = [p for p in products if keyword.lower() in p["name"].lower()]

    if not matched:
        return {"message": "No products matched your search"}

    return {"matched_products": matched, "count": len(matched)}


@app.get("/products/deals")
def product_deals():

    cheapest = min(products, key=lambda x: x["price"])
    expensive = max(products, key=lambda x: x["price"])

    return {"best_deal": cheapest, "premium_pick": expensive}



@app.get("/products/filter")
def filter_products(
        category: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
):

    filtered = products

    if category:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]

    if min_price is not None:
        filtered = [p for p in filtered if p["price"] >= min_price]

    if max_price is not None:
        filtered = [p for p in filtered if p["price"] <= max_price]

    return {"products": filtered, "count": len(filtered)}


@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}

    return {"error": "Product not found"}


@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data)

    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback)
    }


@app.get("/products/summary")
def product_summary():

    total = len(products)
    instock = len([p for p in products if p["in_stock"]])
    outstock = total - instock

    most_expensive = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])

    categories = list(set([p["category"] for p in products]))

    return {
        "total_products": total,
        "in_stock_count": instock,
        "out_of_stock_count": outstock,
        "most_expensive": {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }


@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
            continue

        if not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
            continue

        subtotal = product["price"] * item.quantity
        grand_total += subtotal

        confirmed.append({
            "product": product["name"],
            "qty": item.quantity,
            "subtotal": subtotal
        })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }


@app.post("/orders")
def create_order(order: Order):

    order_data = {
        "id": len(orders) + 1,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "pending"
    }

    orders.append(order_data)

    return order_data


@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["id"] == order_id:
            return order

    return {"error": "Order not found"}


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["id"] == order_id:
            order["status"] = "confirmed"
            return order

    return {"error": "Order not found"}



@app.post("/products", status_code=201)
def add_product(product: Product):

    for p in products:
        if p["name"].lower() == product.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")

    new_product = product.dict()
    new_product["id"] = len(products) + 1

    products.append(new_product)

    return {"message": "Product added", "product": new_product}


@app.put("/products/discount")
def discount_products(category: str, discount_percent: int):

    updated = []

    for p in products:

        if p["category"].lower() == category.lower():

            new_price = int(p["price"] * (1 - discount_percent / 100))

            p["price"] = new_price

            updated.append({"name": p["name"], "new_price": new_price})

    if not updated:
        return {"message": "No products found in this category"}

    return {"updated_products": updated, "count": len(updated)}


@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):

    for p in products:

        if p["id"] == product_id:

            if price is not None:
                p["price"] = price

            if in_stock is not None:
                p["in_stock"] = in_stock

            return {"message": "Product updated", "product": p}

    raise HTTPException(status_code=404, detail="Product not found")


@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    for p in products:

        if p["id"] == product_id:

            products.remove(p)

            return {"message": f"Product '{p['name']}' deleted"}

    raise HTTPException(status_code=404, detail="Product not found")



@app.get("/products/audit")
def products_audit():

    total_products = len(products)

    in_stock = [p for p in products if p["in_stock"]]

    out_stock = [p["name"] for p in products if not p["in_stock"]]

    total_stock_value = sum(p["price"] * 10 for p in in_stock)

    most_expensive = max(products, key=lambda x: x["price"])

    return {
        "total_products": total_products,
        "in_stock_count": len(in_stock),
        "out_of_stock_names": out_stock,
        "total_stock_value": total_stock_value,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        }
    }




