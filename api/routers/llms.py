from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from api.core.dependencies import get_admin_user
from api.schemas.exceptions import GenericException
from api.schemas.llms import LlmCreate, LlmInfo
from api.services.llm import LlmService

router = APIRouter(
    prefix="/llms",
    tags=["llms"],
    dependencies=[Depends(get_admin_user)],  # Only admin users can manage LLMs
    responses={
        403: {"description": "Forbidden", "model": GenericException},
        401: {"description": "Unauthorized", "model": GenericException},
    },
)

r404 = {404: {"description": "Not Found", "model": GenericException}}


@router.get("/", response_model=dict[str, LlmInfo])
async def list_llms(service: Annotated[LlmService, Depends()]):
    return service.list_llms()


@router.get("/llm/{llm_name}", response_model=LlmInfo, responses=r404)
async def get_llm(llm_name: str, service: Annotated[LlmService, Depends()]):
    return service.get_llm(llm_name)


@router.delete("/llm/{llm_name}", responses=r404)
async def delete_llm(llm_name: str, service: Annotated[LlmService, Depends()]):
    service.delete_llm(llm_name)
    return {"message": f"Deleted LLM: {llm_name}"}


@router.patch("/llm/{llm_name}", responses=r404)
async def update_llm(
    service: Annotated[LlmService, Depends()],
    llm_name: str,
    spec: dict[str, Any],
    default: bool = False,
):
    service.update_llm(llm_name, spec, default)
    return {"message": f"Updated LLM: {llm_name}"}


@router.post("/llm", status_code=status.HTTP_201_CREATED)
async def add_llm(service: Annotated[LlmService, Depends()], llm: LlmCreate):
    service.add_llm(llm)
    return {"message": f"Added LLM: {llm.name}"}


@router.get("/vendors")
async def list_vendors(service: Annotated[LlmService, Depends()]):
    return service.list_vendors()


@router.get("/vendor/{vendor_name}", responses=r404)
async def get_vendor_desc(vendor_name: str, service: Annotated[LlmService, Depends()]):
    return service.get_vendor_desc(vendor_name)
