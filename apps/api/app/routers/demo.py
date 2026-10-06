from typing import Literal

from fastapi import APIRouter, Query

from app.services.demo_capacity_health import sprint_08_capacity_health

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


@router.get("/sprint-08/capacity-health")
def get_sprint_08_capacity_health(
    sprint_day: int = Query(10, ge=1, le=10),
    comparison: Literal["since_planning", "since_previous_working_day"] = "since_planning",
    mode: Literal["current_sprint", "retrospective"] = "current_sprint",
) -> dict:
    return sprint_08_capacity_health(sprint_day=sprint_day, comparison=comparison, mode=mode)
