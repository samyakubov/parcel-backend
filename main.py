from dotenv import load_dotenv
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from endpoints.admin import admin_routes
from endpoints.api_keys import api_key_routes
from endpoints.database import database_routes
from endpoints.party import party_routes
from endpoints.property import property_routes
from exception_handlers import register_exception_handlers

load_dotenv()


def get_api_key_identifier(request: Request) -> str:
    """Extract API key or IP for rate limiting."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key[:16]}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_api_key_identifier,
    default_limits=["1000/minute"],
)

app = FastAPI()

app.state.limiter = limiter

app.add_middleware(SlowAPIMiddleware)

register_exception_handlers(app)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for liveness probe"""
    return {"status": "healthy"}

app.include_router(property_routes)
app.include_router(party_routes)
app.include_router(api_key_routes)
app.include_router(admin_routes)
app.include_router(database_routes)
