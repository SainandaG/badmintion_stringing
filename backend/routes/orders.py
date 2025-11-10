# backend/routes/orders.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.neo4j_client import neo4j_client
from backend.services.geocode_client import geocode_address  # Free geocoding
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["orders"])

# ----- Pydantic models -----
class OrderCreate(BaseModel):
    customer_name: str
    racket_id: int | None = None
    issue: str | None = None
    address: str

# ----- Routes -----
@router.post("/create")
async def create_order(order: OrderCreate):
    try:
        # Geocode address
        lat, lon, city = geocode_address(order.address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geocoding failed: {e}")

    order_id = int(datetime.now().timestamp())
    timestamp = datetime.now().isoformat()

    with neo4j_client.driver.session() as session:
        # Merge Customer node
        session.run(
            "MERGE (c:Customer {name:$customer})",
            customer=order.customer_name
        )

        # Merge Order node
        session.run(
            "MERGE (o:Order {order_id:$order_id}) "
            "SET o.issue=$issue, o.status='pending', o.address=$address, "
            "o.lat=$lat, o.lon=$lon, o.city=$city, o.timestamp=$ts",
            order_id=order_id,
            issue=order.issue or "N/A",
            address=order.address,
            lat=lat,
            lon=lon,
            city=city,
            ts=timestamp
        )

        # Link Customer → Order
        session.run(
            "MATCH (c:Customer {name:$customer}), (o:Order {order_id:$order_id}) "
            "MERGE (c)-[:PLACED]->(o)",
            customer=order.customer_name,
            order_id=order_id
        )

        # If racket_id is provided, link Order → Racket
        if order.racket_id:
            session.run(
                "MATCH (o:Order {order_id:$order_id}), (r:Racket {racket_id:$racket_id}) "
                "MERGE (o)-[:RELATES_TO]->(r)",
                order_id=order_id,
                racket_id=order.racket_id
            )

    return {
        "order_id": order_id,
        "customer": order.customer_name,
        "status": "pending",
        "address": order.address,
        "city": city,
        "lat": lat,
        "lon": lon,
        "timestamp": timestamp
    }

@router.get("/customer/{customer_name}")
async def get_customer_orders(customer_name: str):
    with neo4j_client.driver.session() as session:
        result = session.run(
            "MATCH (c:Customer {name:$customer})-[:PLACED]->(o:Order) "
            "OPTIONAL MATCH (o)-[:RELATES_TO]->(r:Racket) "
            "RETURN o.order_id AS order_id, o.status AS status, "
            "o.issue AS issue, o.address AS address, o.city AS city, "
            "o.timestamp AS timestamp, r.brand AS racket_brand, r.type AS racket_type",
            customer=customer_name
        )
        data = result.data()
        if not data:
            raise HTTPException(status_code=404, detail="No orders found")
        return data
