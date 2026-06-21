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
    "You are a helpful assistant for querying NYC property data. "
    "Always start by calling resolve_property to get the BBL for any address or BBL the user mentions. "
    "Then call only the specific tools needed to answer the question — do not fetch data you won't use. "
    "Examples: 'who owns X?' → resolve_property + get_property_owners. "
    "'Any violations at X?' → resolve_property + get_property_violations. "
    "Only call get_full_property_card when the user explicitly asks for a complete property overview. "
    "Summarize results in plain language. Do not show raw JSON or data dumps to the user."
)

_MAX_ITERATIONS = 10


class LLMAgent:
    def __init__(self, db: DatabaseConnector):
        self.db = db
        self.llm = ChatOpenAI(
            model="openai/gpt-oss-120b:free",
            openai_api_key=os.environ["OPENAI_API_KEY"],
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
        )
        self.tools, self._captured = get_tools(self.db)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_map = {t.name: t for t in self.tools}

    def ask(self, question: str, conversation_history: list[ConversationMessage] | None = None) -> AskResponse:
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        for msg in conversation_history or []:
            lc_cls = _ROLE_TO_LC.get(msg.role)
            if lc_cls:
                messages.append(lc_cls(content=msg.content))

        messages.append(HumanMessage(content=question))

        self._captured.clear()
        response = None

        for _ in range(_MAX_ITERATIONS):
            response = self.llm_with_tools.invoke(messages)

            if not response.tool_calls:
                break

            messages.append(response)

            for tool_call in response.tool_calls:
                tool = self.tool_map.get(tool_call["name"])
                if tool is None:
                    messages.append(ToolMessage(f"Unknown tool: {tool_call['name']}", tool_call_id=tool_call["id"]))
                    continue

                messages.append(ToolMessage(str(tool.invoke(tool_call["args"])), tool_call_id=tool_call["id"]))

        answer = response.content if response else ""

        return AskResponse(
            response=answer,
            property_data=self._captured.get("property_data"),
            updated_history=(conversation_history or [])
            + [
                ConversationMessage(role="user", content=question),
                ConversationMessage(role="assistant", content=answer),
            ],
        )
