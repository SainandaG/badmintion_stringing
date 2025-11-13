from pydantic import BaseModel
from typing import Optional

class Agent(BaseModel):
    agent_id: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
