from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from database_connector import DatabaseConnector
from pydantic_models import AskResponse
from services.ai.tools import get_tools


class LLMAgent:
    def __init__(self, db: DatabaseConnector):
        self.db = db
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.tools = get_tools(self.db)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def ask(self, question: str) -> AskResponse:
        messages = [
            SystemMessage(content="You are a helpful assistant for querying property data. "
                                  "Use the available tools to answer the user's question. "
                                  "If you get a JSON response from a tool, parse it and summarize the relevant "
                                  "information for the user in a natural language response. "
                                  "Do not just dump the JSON back to the user."),
            HumanMessage(content=question),
        ]

        property_data = None
        response = self.llm_with_tools.invoke(messages)

        if response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                selected_tool = {t.name: t for t in self.tools}[tool_call["name"]]
                tool_output = selected_tool.invoke(tool_call["args"])

                if isinstance(tool_output, dict):
                    summary_for_llm = tool_output.get("summary", "")
                    property_data = tool_output.get("full_data")
                else:
                    summary_for_llm = str(tool_output)

                messages.append(ToolMessage(summary_for_llm, tool_call_id=tool_call["id"]))

            final_response = self.llm_with_tools.invoke(messages)
            return AskResponse(
                response=final_response.content,
                property_data=property_data
            )

        return AskResponse(
            response=response.content,
            property_data=None
        )
