from typing import Annotated, Any

from fastapi import APIRouter, Depends

from api.core.dependencies import get_current_active_user
from api.schemas.exceptions import GenericException
from api.services.reasoning import ReasoningService

router = APIRouter(
    prefix="/reasonings",
    tags=["reasonings"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        403: {"description": "Forbidden", "model": GenericException},
        401: {"description": "Unauthorized", "model": GenericException},
        404: {"description": "Not Found", "model": GenericException},
    },
)


@router.get("/", response_model=list[str])
async def list_reasonings(service: Annotated[ReasoningService, Depends()]):
    return service.list_reasonings()


@router.get("/{reasoning_name}/config", response_model=dict[str, Any])
async def get_reasoning_config(
    reasoning_name: str, service: Annotated[ReasoningService, Depends()]
):
    return service.get_reasoning_config(reasoning_name)


@router.get("/settings", response_model=dict[str, Any])
async def get_reasoning_app_settings(service: Annotated[ReasoningService, Depends()]):
    return service.get_reasoning_app_settings()
