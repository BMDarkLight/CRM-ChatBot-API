from langgraph.graph import StateGraph
from pymongo import MongoClient
from app.classifier import classifier_node, AgentState
from app.agents.crm_agent import crm_agent_node
from app.agents.unknown import unknown_node
import os

builder = StateGraph(AgentState)

sessions_db = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/")).crm.sessions

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

builder.set_entry_point("classify")

builder.set_finish_point("unknown")
builder.set_finish_point("crm-agent")

graph = builder.compile()