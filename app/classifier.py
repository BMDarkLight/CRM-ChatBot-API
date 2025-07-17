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
        SystemMessage(content="You are a chat history summarizer. If there is no chat history, return nothing. Summarize this chat history:")
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

    if not chat_history:
        system_prompt = (
            "You are a smart classifier. Your job is to categorize a user's question and pass the prompt to the related agent.\n"
            "Return only one word: 'crm-agent' or 'unknown'.\n"
            "Return 'crm-agent' if the prompt is an Imperative sentence or the question is related to customer relationship management, orders, products, support, or user/account actions or it is requesting to pull off an action.\n"
            f"The user just asked: '{question}'. Classify this appropriately."
        )
    else:
        system_prompt = (
            "You are a smart classifier. Your job is to categorize a user's question and pass the prompt to the related agent.\n"
            "Return only one word: 'crm-agent' or 'unknown'.\n"
            "Return 'crm-agent' if the prompt is an Imperative sentence or the question is related to customer relationship management, orders, products, support, or user/account actions or it is requesting to pull off an action.\n"
            "عبارت 'crm-agent' را برگردان اگر پرامپت کاربر یک جمله ی امری است یا کاربر درخواست انجام کاری را انجام داده است یا سوال مرتبط به سیستم CRM، کاریز ها، پشتیبانی، محصولات، سفارشات یا کاربران و مشتریان است.\n"
            "If it doesn't clearly fit into those, return 'unknown'.\n"
            f"Here is a summary of the chat history:\n{summary.content.strip()}\n"
            f"The last question asked by the user is: '{last_entry_question}' and the {last_entry_agent} answered: '{last_entry_answer}'."
            " If this new question is a follow-up or continuation, return the same agent. Otherwise, classify the new question."
        )

    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ])

    raw_output = response.content.strip().lower()
    label = raw_output if raw_output in {"crm-agent"} else "unknown"

    return {**state, "agent": label}