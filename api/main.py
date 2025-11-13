import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, Security
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.core.config import settings
from api.routers import agents, auth, conversations, embeddings, llms, rerankings, chat, index, reasonings

# Definición del esquema de seguridad (no implementa la validación, solo define cómo se envía el token)
security = HTTPBearer()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 2. Configuración de CORS
# ************ CORRECCIÓN IMPORTANTE ************
# Se usa el comodín "*" para desarrollo en LAN, ya que las IPs dinámicas no están en la lista.
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Now restricted to the list above
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Fin de la configuración de CORS

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
