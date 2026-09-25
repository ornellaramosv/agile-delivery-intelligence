from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.demo import router as demo_router

app = FastAPI(title="ADI API")
app.include_router(health_router)
app.include_router(demo_router)
