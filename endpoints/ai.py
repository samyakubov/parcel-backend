from fastapi import APIRouter, Depends, HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from database_connector import DatabaseConnector, get_db
from endpoint_handlers.property_search.search_by_property_address import (
    search_by_property_address,
)
from endpoint_handlers.property_search.search_by_property_bbl import (
    search_by_property_bbl,
)
from logger_config import logger
from pydantic_models import AskRequest, AskResponse

ai_routes = APIRouter(prefix="/ai")

def get_tools(db: DatabaseConnector):
    @tool
    def lookup_property_by_address(address: str) -> str:
        """
        Search for property details using its address. 
        Useful for finding owners, violations, zoning, and other usage details for a specific address.
        """
        try:
            result = search_by_property_address(address, db)
            
            # Create a summary to avoid hitting token limits with large history
            summary = {
                "address": address,
                "owners": result.owners.model_dump(),
                "last_sold": result.last_sold.model_dump() if result.last_sold else None,
                "zoning": result.zoning.model_dump() if result.zoning else None,
                "coordinates": result.coordinates.model_dump() if result.coordinates else None,
                "mortgage": result.mortgage.model_dump() if result.mortgage else None,
                "violation_count": len(result.violations),
                "complaint_count": len(result.complaints),
                "record_count": len(result.records),
                "job_filing_count": len(result.job_filings),
                # Include latest 5 records/violations if needed, or just keep it high level
                "latest_violation": result.violations[0].model_dump() if result.violations else None,
                "latest_record": result.records[0].model_dump() if result.records else None,
            }
            return str(summary)
        except Exception as e:
            return f"Error searching for property: {str(e)}"

    @tool
    def lookup_property_by_bbl(bbl: str) -> str:
        """
        Search for property details using its BBL (Borough-Block-Lot).
        BBL is a unique identifier URL for NYC properties. Format is usually a 10-digit string.
        Useful when the user provides a BBL directly.
        """
        try:
            result = search_by_property_bbl(bbl, db)
            # Reuse similar summary logic
            summary = {
                "bbl": bbl,
                "owners": result.owners.model_dump(),
                "last_sold": result.last_sold.model_dump() if result.last_sold else None,
                "zoning": result.zoning.model_dump() if result.zoning else None,
                "coordinates": result.coordinates.model_dump() if result.coordinates else None,
                "mortgage": result.mortgage.model_dump() if result.mortgage else None,
                "violation_count": len(result.violations),
                "complaint_count": len(result.complaints),
                "record_count": len(result.records),
                "job_filing_count": len(result.job_filings),
                "latest_violation": result.violations[0].model_dump() if result.violations else None,
                "latest_record": result.records[0].model_dump() if result.records else None,
            }
            return str(summary)
        except Exception as e:
            return f"Error searching for property by BBL: {str(e)}"


    return [lookup_property_by_address, lookup_property_by_bbl]

@ai_routes.post("/ask", response_model=AskResponse)
async def ask_ai(request: AskRequest, db: DatabaseConnector = Depends(get_db)):
    """
    Ask a question to the AI agent, which has access to property data tools.
    """
    try:
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        tools = get_tools(db)
        llm_with_tools = llm.bind_tools(tools)

        messages = [
            SystemMessage(content="""You are a helpful assistant for querying property data. 
            Use the available tools to answer the user's question. 
            If you get a JSON response from a tool, parse it and summarize the relevant information for the user in a natural language response.
            Do not just dump the JSON back to the user."""),
            HumanMessage(content=request.question),
        ]

        # Simple tool calling loop
        response = llm_with_tools.invoke(messages)
        
        # Check if the model decided to call a tool
        if response.tool_calls:
            messages.append(response) # Add the assistant's message with tool call
            for tool_call in response.tool_calls:
                selected_tool = {t.name: t for t in tools}[tool_call["name"]]
                tool_output = selected_tool.invoke(tool_call["args"])
                
                # Append tool output to messages
                messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))
            
            # Get final response after tool execution
            final_response = llm_with_tools.invoke(messages)
            return AskResponse(response=final_response.content)
        
        # If no tool called, just return the content
        return AskResponse(response=response.content)

    except Exception as e:
        logger.error(f"Error in /ai/ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
