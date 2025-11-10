from pydantic import BaseModel
from typing import Optional

class Order(BaseModel):
    order_id: str
    customer_name: str
    customer_address: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    assigned_agent: Optional[str] = None
    status: str = "pending"
