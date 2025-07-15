from langchain_openai import ChatOpenAI
from langsmith import traceable
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import TypedDict, Literal

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

AgentType = Literal["crm-agent", "unknown"]

class ChatHistoryEntry(TypedDict):
    user: str
    assistant: str
    agent: AgentType

class AgentState(TypedDict, total=False):
    question: str
    chat_history: list[ChatHistoryEntry]
    session_id: str
    agent: AgentType
    answer: str

@traceable
def classifier_node(state: AgentState) -> AgentState:
    question = state.get("question", "").strip()

    summerizer = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    chat_history = state.get("chat_history", [])

    summary_messages = [
        SystemMessage(content="You are a chat history summarizer. Summarize this chat history:")
    ]

    for user, assistant in chat_history:
        summary_messages.append(HumanMessage(content=user))
        summary_messages.append(AIMessage(content=assistant))

    summary = summerizer.invoke(summary_messages)

    last_entry = chat_history[-1] if chat_history else None
    if last_entry != None:
        if isinstance(last_entry, dict):
            last_entry_question = last_entry['user']
            last_entry_answer = last_entry['assistant']
            last_entry_agent = last_entry['agent']
        else:
            last_entry_question = last_entry[0] if len(last_entry) > 0 else ""
            last_entry_answer = last_entry[1] if len(last_entry) > 1 else ""
            last_entry_agent = "unknown"

    system_prompt = (
        "You are a smart classifier. Your job is to categorize a user's question as pass the prompt the related agent."
        "into one of the following topics: crm-agent.\n"
        "Return only one word as response."
        "Return crm-agent if the question is related to customer relationship management entries, questions about orders, products, or customer support."
        "If it doesn't clearly fit into the agents described, return 'unknown'."
        "Your responses should be either 'crm-agent', 'unknown' regardless of the prompt you receive after this."
        "Here is a summary of the chat history:\n"
        f"{summary.content.strip()}\n"
        f"The last question asked by the user is {last_entry_question} and the {last_entry_agent} answered with {last_entry_answer}, if this needs a continuation by the same agent, return that agent to answer" if last_entry != None else ""
    )

    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ])

    raw_output = response.content.strip().lower()
    label = raw_output if raw_output in {"crm-agent"} else "unknown"

    return {**state, "agent": label}