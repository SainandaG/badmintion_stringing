from fastapi import APIRouter, HTTPException
from fastapi import Body
from backend.services.llm_agent import llm_client
from backend.services.neo4j_client import neo4j_client

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

@router.post("/assign_agent/{order_id}")
async def assign_agent(order_id: str):
    # Fetch order details
    order = neo4j_client.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Decide agent assignment via AI
    agent_id = llm_client.assign_agent(order)
    neo4j_client.assign_order_to_agent(order_id, agent_id)
    
    return {"message": f"Order {order_id} assigned to agent {agent_id}"}


@router.post("/chat")
async def chat_with_ai(payload: dict = Body(...)):
    user_message = payload.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    response = llm_client.chat(user_message)
    return {"response": response}
