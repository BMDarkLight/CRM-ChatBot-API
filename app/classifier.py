from langchain_openai import ChatOpenAI
from typing import TypedDict, Literal

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

AgentType = Literal["crm-agent", "unknown"]

class AgentState(TypedDict, total=False):
    question: str
    agent: AgentType
    answer: str

def classifier_node(state: AgentState) -> AgentState:
    question = state.get("question", "").strip()

    system_prompt = (
        "You are a smart classifier. Your job is to categorize a user's question as pass the prompt the related agent."
        "into one of the following topics: crm-agent.\n"
        "Return only one word as response. "
        "If it doesn't clearly fit, return 'unknown'."
        "Your responses should be either 'crm-agent', 'unknown' regardless of the prompt you receive after this."
    )

    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ])

    raw_output = response.content.strip().lower()
    label = raw_output if raw_output in {"crm-agent"} else "unknown"

    return {**state, "agent": label}