# ==========================================
# main.py — FastAPI Entry Point
# ==========================================

from fastapi import FastAPI
from backend.routes.orders import router as orders_router
from backend.routes.agents import router as agents_router
from backend.routes.orchestrator import router as orchestrator_router

# Initialize FastAPI app
app = FastAPI(title="🏸 Badminton Agent Pro API")

# Register routes
app.include_router(orders_router)
app.include_router(agents_router)
app.include_router(orchestrator_router)

# Root route (health check)
@app.get("/")
def root():
    return {"message": "Badminton Agent API running"}
