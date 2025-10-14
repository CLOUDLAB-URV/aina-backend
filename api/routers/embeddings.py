from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from api.core.dependencies import get_admin_user
from api.schemas.embeddings import EmbeddingCreate, EmbeddingInfo
from api.schemas.exceptions import GenericException
from api.services.embedding import EmbeddingService

router = APIRouter(
    prefix="/embeddings",
    tags=["embeddings"],
    dependencies=[Depends(get_admin_user)],  # Only admin users can manage embeddings
    responses={
        403: {"description": "Forbidden", "model": GenericException},
        401: {"description": "Unauthorized", "model": GenericException},
    },
)

r404 = {404: {"description": "Not Found", "model": GenericException}}


@router.get("/", response_model=dict[str, EmbeddingInfo])
async def list_embeddings(service: Annotated[EmbeddingService, Depends()]):
    return service.list_embeddings()


@router.get("/embedding/{embedding_name}", response_model=EmbeddingInfo, responses=r404)
async def get_embedding(
    embedding_name: str, service: Annotated[EmbeddingService, Depends()]
):
    return service.get_embedding(embedding_name)


@router.delete("/embedding/{embedding_name}", responses=r404)
async def delete_embedding(
    embedding_name: str, service: Annotated[EmbeddingService, Depends()]
):
    service.delete_embedding(embedding_name)
    return {"message": f"Deleted embedding: {embedding_name}"}


@router.patch("/embedding/{embedding_name}", responses=r404)
async def update_embedding(
    embedding_name: str,
    spec: dict[str, Any],
    service: Annotated[EmbeddingService, Depends()],
):
    service.update_embedding(embedding_name, spec)
    return {"message": f"Updated embedding: {embedding_name}"}


@router.post("/embedding", status_code=status.HTTP_201_CREATED)
async def add_embedding(
    embedding: EmbeddingCreate, service: Annotated[EmbeddingService, Depends()]
):
    service.add_embedding(embedding)
    return {"message": f"Added embedding: {embedding.name}"}


@router.get("/vendors")
async def list_embedding_vendors(service: Annotated[EmbeddingService, Depends()]):
    return service.list_vendors()


@router.get("/vendor/{vendor_name}", responses=r404)
async def get_embedding_vendor_desc(
    vendor_name: str, service: Annotated[EmbeddingService, Depends()]
):
    return service.get_vendor_desc(vendor_name)
