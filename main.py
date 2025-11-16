from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from database_connector import DatabaseConnector
from endpoint_handlers.api_keys.init_key_table import init_key_table
from endpoints.property import property_routes
from exception_handlers import register_exception_handlers
from endpoints.api_keys import api_key_routes

load_dotenv()
app = FastAPI()


def get_db():
    db = DatabaseConnector("nycdb.duckdb")
    try:
        db.connect()
        yield db
    finally:
        db.close()


register_exception_handlers(app)
init_key_table()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(property_routes)
app.include_router(api_key_routes)
