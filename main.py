from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from endpoints.admin import admin_routes
from endpoints.api_keys import api_key_routes
from endpoints.property import property_routes
from exception_handlers import register_exception_handlers

load_dotenv()
app = FastAPI()

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(property_routes)
app.include_router(api_key_routes)
app.include_router(admin_routes)
