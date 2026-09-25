from fastapi import APIRouter

from app.services.demo_quality_rework import sprint_08_quality_rework

from app.services.demo_burndown import sprint_08_burndown
from app.services.demo_delivery_flow import sprint_08_delivery_flow

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/sprint-08/burndown")
def get_sprint_08_burndown() -> dict:
    return sprint_08_burndown()


@router.get("/sprint-08/delivery-flow")
def get_sprint_08_delivery_flow() -> dict:
    return sprint_08_delivery_flow()


@router.get("/sprint-08/quality-rework")
def get_sprint_08_quality_rework() -> dict:
    return sprint_08_quality_rework()
