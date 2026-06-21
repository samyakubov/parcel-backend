from fastapi import APIRouter, Depends, HTTPException

from database_connector import DatabaseConnector, get_db
from logger_config import logger
from schemas import AskRequest, AskResponse
from services.ai.llm_agent import LLMAgent

ai_routes = APIRouter(prefix="/ai")

@ai_routes.post("/ask", response_model=AskResponse)
async def ask_ai(request: AskRequest, db: DatabaseConnector = Depends(get_db)):
    """
    Ask a question to the AI agent, which has access to property data tools.
    """
    try:
        agent = LLMAgent(db)
        response = agent.ask(request.question, request.conversation_history)
        return response
    except Exception as e:
        logger.error(f"Error in /ai/ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
