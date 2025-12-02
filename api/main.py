from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from theflow.settings import settings as flowsettings

from api.core.config import settings
from api.routers import (
    agents,
    auth,
    chat,
    conversations,
    embeddings,
    index,
    llms,
    reasonings,
    rerankings,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

if hasattr(flowsettings, "CORS_ORIGINS"):
    CORS = flowsettings.CORS_ORIGINS
else:
    CORS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(PermissionError)
async def permission_error_exception_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=403,
        content={"detail": f"Permission error: {exc}"},
    )


@app.exception_handler(LookupError)
async def lookup_error_exception_handler(request: Request, exc: LookupError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Lookup error: {exc}"},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Value error: {exc}"},
    )


@app.exception_handler(AttributeError)
async def attribute_error_exception_handler(request: Request, exc: AttributeError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Attribute error: {exc}"},
    )


@app.exception_handler(TypeError)
async def type_error_exception_handler(request: Request, exc: TypeError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Type error: {exc}"},
    )


app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(llms.router, prefix=settings.API_V1_STR)
app.include_router(embeddings.router, prefix=settings.API_V1_STR)
app.include_router(rerankings.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(agents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(index.router, prefix=settings.API_V1_STR)
app.include_router(reasonings.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
