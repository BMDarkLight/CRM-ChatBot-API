from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langsmith import traceable
from app.classifier import AgentState
from app.crm_client import CRMClient
import os

@traceable
def crm_agent_node(state: AgentState) -> AgentState:
    crm_client = CRMClient(api_key=os.environ.get("DIDAR_API_KEY"))
    
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    summerizer = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    chat_history = state.get("chat_history", [])

    summary_messages = [
        SystemMessage(content="You are a chat history summarizer. Summarize this chat history:")
    ]

    for user, assistant in chat_history:
        summary_messages.append(HumanMessage(content=user))
        summary_messages.append(AIMessage(content=assistant))

    summary = summerizer.invoke(summary_messages)

    messages = [
        SystemMessage(
            content=(
                "You are an AI agent in a smart Chatbot API for an online shop, designed to handle customer relationship management (CRM) queries. "
                "You are the crm-agent, which means you are responsible for handling CRM-related questions. "
                "You have access to tools that connect to DIDAR CRM API, which allows you to search for users, get user details, and update user information. "
                "Don't try to answer questions that aren't related to shopping or customer relations or users. "
                "You are specified to answer only CRM related questions, strictly only answer CRM related questions."
                f"The chat history is summarized as follows: {summary.content}"
            )
        )
    ]

    tools = []

    for user, assistant in chat_history:
        messages.append(HumanMessage(content=user))
        messages.append(AIMessage(content=assistant))

    messages.append(HumanMessage(content=state["question"]))
    response = llm(
        messages,
        tools=tools,
        tool_choice="auto",
    )

    if "chat_history" not in state:
        state["chat_history"] = []

    state["chat_history"].append((state["question"], response.content))

    return {
        **state,
        "answer": response.content
    }