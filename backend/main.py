# main.py - FastAPI entry point
from fastapi import FastAPI
from fastapi import FastAPI
from backend.routes.orders import router as orders_router
from backend.routes.agents import router as agents_router
from backend.routes.orchestrator import router as orchestrator_router

app = FastAPI()
app.include_router(orders_router)
app.include_router(agents_router)
app.include_router(orchestrator_router)

app = FastAPI()

# import routers here
from fastapi import FastAPI
from backend.routes.orders import router as orders_router
from backend.routes.orchestrator import router as orchestrator_router

app = FastAPI(title="Badminton Agent Pro")

app.include_router(orders_router)
app.include_router(orchestrator_router)

@app.get("/")
def root():
    return {"message": "Badminton Agent API running"}
