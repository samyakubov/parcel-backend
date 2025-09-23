from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from endpoints.property import property_routes

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(property_routes)

