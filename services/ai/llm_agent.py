import os

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from database_connector import DatabaseConnector
from schemas import AskResponse, ConversationMessage
from services.ai.tools import get_tools

_ROLE_TO_LC = {
    "user": HumanMessage,
    "assistant": AIMessage,
}

SYSTEM_PROMPT = (
    "You are a helpful assistant for querying property data. "
    "Use the available tools to answer the user's question. "
    "If you get a JSON response from a tool, parse it and summarize the relevant "
    "information for the user in a natural language response. "
    "Do not just dump the JSON back to the user."
)


class LLMAgent:
    def __init__(self, db: DatabaseConnector):
        self.db = db
        self.llm = ChatOpenAI(
            model="openai/gpt-oss-120b:free",
            openai_api_key=os.environ["OPENAI_API_KEY"],
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
        )
        self.tools = get_tools(self.db)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def ask(self, question: str, conversation_history: list[ConversationMessage] | None = None) -> AskResponse:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        for msg in (conversation_history or []):
            lc_cls = _ROLE_TO_LC.get(msg.role)
            if lc_cls:
                messages.append(lc_cls(content=msg.content))

        messages.append(HumanMessage(content=question))

        history_out = [m for m in (conversation_history or [])]

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
            answer = final_response.content
        else:
            answer = response.content

        history_out.append(ConversationMessage(role="user", content=question))
        history_out.append(ConversationMessage(role="assistant", content=answer))

        return AskResponse(
            response=answer,
            property_data=property_data,
            updated_history=history_out,
        )
