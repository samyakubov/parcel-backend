from fastapi import APIRouter, Depends

from database_connector import DatabaseConnector, get_db
from endpoint_handlers.database.database_stats import database_stats

database_routes = APIRouter(prefix="/database")

@database_routes.get("/stats")
async def get_database_stats(db: DatabaseConnector = Depends(get_db)):
    return database_stats(db)

