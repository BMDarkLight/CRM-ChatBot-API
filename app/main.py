from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from app.agent import graph
from dotenv import load_dotenv
import getpass
import os

app = FastAPI()

load_dotenv()

sysprompt = """
You are a smart Chatbot API for an online shop, designed to handle customer relationship management (CRM) queries.
"""

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

if "LANGSMITH_API_KEY" not in os.environ:
    os.environ["LANGSMITH_API_KEY"] = getpass.getpass("Enter your LangSmith API key: ")

if "DIDAR_API_KEY" not in os.environ:
    os.environ["DIDAR_API_KEY"] = getpass.getpass("Enter your Didar API key: ")

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <html>
        <head>
            <title>🛒 CRM Chatbot API for Online Shop</title>
        </head>
        <body>
            <h1>🛒 CRM Chatbot API for Online Shop</h1>
            <p>This project implements an AI-powered chatbot API for customer relationship management (CRM) in an online shop, seamlessly integrated with Didar CRM. It leverages advanced language model orchestration with LangChain and LangGraph, includes robust LangSmith tracing for monitoring agent behavior, and uses FastAPI for a high-performance web API layer. The project is fully containerized with Docker and supports on-demand testing via GitHub Actions.</p>
            <h1>API Documentation</h1>
            <p>To explore the API documentation, visit <a href="/docs">/docs</a></p>
            <p>To access the OpenAPI schema, visit <a href="/openapi.json">/openapi.json</a></p>
            <h1>GitHub Repository</h1>
            <p>For source code and contributions, visit the <a href="https://github.com/BMDarkLight/CRM-ChatBot-API">GitHub repository</a>.</p>
        </body>
    </html>
    """

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": True})

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    agent: str
    response: str

@app.get("/ask", response_model=QueryResponse)
def ask(query: QueryRequest):
    if not query.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    state = {"question": query.query}
    result = graph.invoke(state)
    return QueryResponse(
        agent = result["agent"],
        response = result.get("answer", "No answer provided")
    )