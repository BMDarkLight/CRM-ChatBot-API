import os
from langchain_openai import ChatOpenAI
from app.classifier import AgentState
from app.crm_client import CRMClient

def crm_agent_node(state: AgentState) -> AgentState:
    crm_client = CRMClient(api_key=os.environ.get("DIDAR_API_KEY"))

    return state