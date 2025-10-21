from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from api.core.dependencies import get_admin_user
from api.schemas.exceptions import GenericException
from api.schemas.rerankings import RerankingCreate, RerankingInfo
from api.services.reranking import RerankingService

router = APIRouter(
    prefix="/rerankings",
    tags=["rerankings"],
    dependencies=[Depends(get_admin_user)],  # Only admin users can manage rerankings
    responses={
        403: {"description": "Forbidden", "model": GenericException},
        401: {"description": "Unauthorized", "model": GenericException},
        404: {"description": "Not Found", "model": GenericException},
    },
)


@router.get("/", response_model=dict[str, RerankingInfo])
async def list_rerankings(service: Annotated[RerankingService, Depends()]):
    return service.list_rerankings()


@router.get("/reranking/{reranking_name}", response_model=RerankingInfo)
async def get_reranking(
    reranking_name: str, service: Annotated[RerankingService, Depends()]
):
    return service.get_reranking(reranking_name)


@router.delete("/reranking/{reranking_name}")
async def delete_reranking(
    reranking_name: str, service: Annotated[RerankingService, Depends()]
):
    service.delete_reranking(reranking_name)
    return {"message": f"Deleted reranking: {reranking_name}"}


@router.patch("/reranking/{reranking_name}")
async def update_reranking(
    service: Annotated[RerankingService, Depends()],
    reranking_name: str,
    spec: dict[str, Any],
    default: bool = False,
):
    service.update_reranking(reranking_name, spec, default)
    return {"message": f"Updated reranking: {reranking_name}"}


@router.post("/reranking", status_code=status.HTTP_201_CREATED)
async def add_reranking(
    reranking: RerankingCreate, service: Annotated[RerankingService, Depends()]
):
    service.add_reranking(reranking)
    return {"message": f"Added reranking: {reranking.name}"}


@router.get("/vendors")
async def list_reranking_vendors(service: Annotated[RerankingService, Depends()]):
    return service.list_vendors()


@router.get("/vendor/{vendor_name}")
async def get_reranking_vendor_desc(
    vendor_name: str, service: Annotated[RerankingService, Depends()]
):
    return service.get_vendor_desc(vendor_name)
