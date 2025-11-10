from fastapi import APIRouter, HTTPException
from backend.models.agent import Agent
from backend.services.neo4j_client import neo4j_client

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/create")
async def create_agent(agent: Agent):
    neo4j_client.create_agent(agent.agent_id, agent.name, agent.lat, agent.lon)
    return {"message": "Agent created successfully", "agent": agent.dict()}

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agent = neo4j_client.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
