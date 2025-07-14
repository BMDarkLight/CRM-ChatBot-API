from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from dotenv import load_dotenv
from app.agent import graph, sessions_db
from app.auth import create_access_token, verify_token, users_db
import uuid

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/signin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def admin_required(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if user.get("permission") != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")
    return True

load_dotenv()

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": True})

@app.post("/signup")
def signup(form_data: OAuth2PasswordRequestForm = Depends()):
    if users_db.find_one({"username": form_data.username}):
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_password = pwd_context.hash(form_data.password)

    users_db.insert_one({
        "username": form_data.username,
        "password": hashed_password,
        "permission": "user"
    })
    return {"message": "User created successfully"}

@app.post("/signin")
def signin(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.find_one({"username": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}





@app.get("/users", response_model=List[dict])
def list_users(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    if user.get("permission") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    users = list(users_db.find({}, {"_id": 0, "password": 0}))
    return users

@app.get("/users/{username}")
def get_user(username: str, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    if user.get("permission") != "admin" or user["username"] != username:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    user_data = users_db.find_one({"username": username}, {"_id": 0, "password": 0})

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_data

@app.delete("/users/{username}")
def delete_user(username: str, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated") 
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    if user.get("permission") != "admin" or user["username"] != username:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = users_db.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    resultsession = sessions_db.delete_many({"user_id": str(user["_id"])})
    
    return {"message": f"User '{username}' and {resultsession.deleted_count} session(s) deleted successfully"}

@app.get("/sessions", response_model=List[dict])
def list_sessions(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    sessions = list(sessions_db.find({"user_id": str(user["_id"])}, {"_id": 0}))
    return sessions

@app.get("/sessions/{session_id}", response_model=dict)
def get_session(session_id: str, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    session = sessions_db.find_one({"session_id": session_id, "user_id": str(user["_id"])}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    result = sessions_db.delete_one({"session_id": session_id}, {"user_id": user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": f"Session '{session_id}' deleted successfully"}

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    agent: str
    response: str

@app.post("/ask", response_model=QueryResponse)
def ask(query: QueryRequest, token: str = Depends(oauth2_scheme)):
    session_id = query.session_id or str(uuid.uuid4())
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    if not query.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    session = sessions_db.find_one({"session_id": session_id})
    if session and session.get("user_id") != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Permission denied for this session")
    
    chat_history = session.get("chat_history", []) if session else []

    state = {
        "question": query.query,
        "chat_history": chat_history,
        "session_id": session_id,
        "user_id": str(user["_id"])
    }

    result = graph.invoke(state)

    sessions_db.update_one(
        {"session_id": session_id},
        {"$set": {
            "chat_history": result["chat_history"],
            "user_id": user["_id"]
        }},
        upsert=True
    )

    return QueryResponse(
        agent = result["agent"],
        response = result.get("answer", "No answer provided")
    )

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <html>
        <head>
            <title>🛒 CRM Chatbot API for Online Shop</title>
            <meta charset="UTF-8" />
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px;">
            <h1>🛒 CRM Chatbot API for Online Shop</h1>
            <p>This project implements an AI-powered chatbot API for customer relationship management (CRM) in an online shop, seamlessly integrated with Didar CRM. It leverages advanced language model orchestration with LangChain and LangGraph, includes robust LangSmith tracing for monitoring agent behavior, and uses FastAPI for a high-performance web API layer. The project is fully containerized with Docker and supports on-demand testing via GitHub Actions.</p>
            <h1>API Documentation</h1>
            <p>To access the Chatbot, <a href="/chatbot">Click here</a>.</p>
            <p>To access the API, <a href="/login">Login Here</a>.</p>
            <p>To explore the API documentation, Visit <a href="/docs">Documentation</a></p>
            <h1>GitHub Repository</h1>
            <p>For source code and contributions, visit the <a href="https://github.com/BMDarkLight/CRM-ChatBot-API">GitHub repository</a>.</p>
        </body>
    </html>
    """

@app.get("/login", response_class=HTMLResponse)
def login():
    return """
    <html>
        <head>
            <title>API Login</title>
            <meta charset="UTF-8" />
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px;">
            <h1>Login</h1>
            <div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 20px; margin: 20px; border-radius: 10px;background-color: #f9f9f9; text-align: center;">
                <form id="login-form" style="display: inline-block;">
                    <label for="login-username">Username:</label>
                    <input type="text" id="login-username" name="username" required></p>
                    <p><label for="login-password">Password:</label>
                    <input type="password" id="login-password" name="password" required></p>
                    <button type="submit">Sign In</button>
                </form>
            </div>

            <h1>Sign Up</h1>
            <div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 20px; margin: 20px; border-radius: 10px;background-color: #f9f9f9; text-align: center;">
                <form id="signup-form" style="display: inline-block;">
                    <p><label for="signup-username">Username:</label>
                    <input type="text" id="signup-username" name="username" required></p>
                    <p><label for="signup-password">Password:</label>
                    <input type="password" id="signup-password" name="password" required></p>
                    <button type="submit">Sign Up</button>
                </form>
            </div>

            <pre id="output"></pre>

            <script>
            document.getElementById("login-form").addEventListener("submit", async function(e) {
                e.preventDefault();
                const username = document.getElementById("login-username").value;
                const password = document.getElementById("login-password").value;
                const formData = new URLSearchParams();
                formData.append("username", username);
                formData.append("password", password);

                const response = await fetch("/signin", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: formData
                });

                const result = await response.json();
                document.getElementById("output").textContent = JSON.stringify(result, null, 2);
            });

            document.getElementById("signup-form").addEventListener("submit", async function(e) {
                e.preventDefault();
                const username = document.getElementById("signup-username").value;
                const password = document.getElementById("signup-password").value;
                const formData = new URLSearchParams();
                formData.append("username", username);
                formData.append("password", password);

                const response = await fetch("/signup", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: formData
                });

                const result = await response.json();
                document.getElementById("output").textContent = JSON.stringify(result, null, 2);
            });
            </script>
        </body>
    </html>
    """

@app.get("/chatbot", response_class=HTMLResponse)
def chatbot():
    return """
    <html>
        <head>
            <title>Chatbot Interface</title>
            <meta charset="UTF-8" />
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px;">
            <h1>CRM Chatbot Interface</h1>

            <div id="auth-section">
                <h2>Login</h2>
                <div id="login-container" style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 20px; margin: 20px; border-radius: 10px;background-color: #f9f9f9; text-align: center;">
                    <form id="login-form">
                        <label>Username: <input type="text" id="login-username" required></label><br>
                        <label>Password: <input type="password" id="login-password" required></label><br>
                        <button type="submit">Login</button>
                    </form>
                </div>
                <pre id="auth-output"></pre>
            </div>

            <div id="chat-container" style="display: none; border: 1px solid #ccc;">
                <div id="chat-history" style="max-height: 400px; overflow-y: auto; margin-bottom: 20px;"></div>
                <input type="text" id="user-input" placeholder="Type your message here..." style="width: 100%; padding: 10px; box-sizing: border-box;">
                <button id="send-button">Send</button>
            </div>

            <script>
            const sessionId = Math.random().toString(36).substring(2, 18);

            document.getElementById("login-form").addEventListener("submit", async function(e) {
                e.preventDefault();
                const username = document.getElementById("login-username").value;
                const password = document.getElementById("login-password").value;
                const formData = new URLSearchParams();
                formData.append("username", username);
                formData.append("password", password);

                const response = await fetch("/signin", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: formData
                });

                const result = await response.json();
                if (response.ok) {
                    localStorage.setItem("access_token", result.access_token);
                    document.getElementById("auth-section").style.display = "none";
                    document.getElementById("chat-container").style.display = "block";
                }
                document.getElementById("auth-output").textContent = JSON.stringify(result, null, 2);
            });

            document.getElementById("send-button").addEventListener("click", async function() {
                const token = localStorage.getItem("access_token");
                const userInput = document.getElementById("user-input").value;

                if (!token || !userInput) {
                    alert("Missing token or input.");
                    return;
                }

                const response = await fetch("/ask", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token
                    },
                    body: JSON.stringify({ query: userInput, session_id: sessionId })
                });

                const result = await response.json();
                if (!response.ok) {
                    alert("Error: " + result.detail);
                    return;
                }

                const chatHistory = document.getElementById("chat-history");
                chatHistory.innerHTML += `<div><b>You:</b> ${userInput}</div>`;
                chatHistory.innerHTML += `<div><b>Bot (${result.agent}):</b> ${result.response}</div>`;
                document.getElementById("user-input").value = "";
                chatHistory.scrollTop = chatHistory.scrollHeight;
            });
            </script>
        </body>
    </html>
    """
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="CRM Chatbot API",
        version="1.0.0",
        description="AI-powered CRM Chatbot integrated with Didar CRM",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi