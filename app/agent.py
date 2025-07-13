from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from app.main import sysprompt
from app.classifier import classifier_node, AgentState
from app.agents.crm_agent import crm_agent_node

builder = StateGraph(AgentState)

def unknown_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    response = llm([HumanMessage(content=sysprompt + state["question"])])
    return {
        **state,
        "answer": response.content
    }

builder.add_node("classify", classifier_node)
builder.add_node("crm-agent", crm_agent_node)
builder.add_node("unknown", unknown_node)

builder.add_conditional_edges(
    "classify",
    lambda state: state["agent"],
    {
        "crm-agent": "crm-agent",
        "unknown": "unknown"
    }
)

builder.set_finish_point("unknown")
builder.set_finish_point("crm-agent")

graph = builder.compile()