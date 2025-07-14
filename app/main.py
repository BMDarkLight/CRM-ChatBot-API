from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
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

def admin_required(token: str = Depends(oauth2_scheme)):
    user = verify_token(token)
    if user.get("permission") != "admin":
        raise HTTPException(status_code=403, detail="Admin permission required")
    return True

load_dotenv()

@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <html>
        <head>
            <title>🛒 CRM Chatbot API for Online Shop</title>
            <meta charset="UTF-8" />
        </head>
        <body>
            <h1>🛒 CRM Chatbot API for Online Shop</h1>
            <p>This project implements an AI-powered chatbot API for customer relationship management (CRM) in an online shop, seamlessly integrated with Didar CRM. It leverages advanced language model orchestration with LangChain and LangGraph, includes robust LangSmith tracing for monitoring agent behavior, and uses FastAPI for a high-performance web API layer. The project is fully containerized with Docker and supports on-demand testing via GitHub Actions.</p>
            <h1>API Documentation</h1>
            <p>To explore the API documentation, visit <a href="/docs">/docs</a></p>
            <p>To access the OpenAPI schema, visit <a href="/openapi.json">/openapi.json</a></p>
            <p>To access the API, <a href="/login">Login Here</a>.</p>
            <h1>GitHub Repository</h1>
            <p>For source code and contributions, visit the <a href="https://github.com/BMDarkLight/CRM-ChatBot-API">GitHub repository</a>.</p>
        </body>
    </html>
    """

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

@app.get("/login", response_class=HTMLResponse)
def login():
    return """
<html>
    <head>
        <title>API Login</title>
        <meta charset="UTF-8" />
    </head>
    <body>
        <h1>Login</h1>
        <form id="login-form">
            <label for="login-username">Username:</label>
            <input type="text" id="login-username" name="username" required>
            <label for="login-password">Password:</label>
            <input type="password" id="login-password" name="password" required>
            <button type="submit">Sign In</button>
        </form>

        <h1>Sign Up</h1>
        <form id="signup-form">
            <label for="signup-username">Username:</label>
            <input type="text" id="signup-username" name="username" required>
            <label for="signup-password">Password:</label>
            <input type="password" id="signup-password" name="password" required>
            <button type="submit">Sign Up</button>
        </form>

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

class UserRequest(BaseModel):
    token: str = Depends(oauth2_scheme)

@app.get("/users", response_model=List[dict])
def list_users(UserRequest: UserRequest):
    token = UserRequest.token
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
def get_user(username: str,UserRequest: UserRequest):
    token = UserRequest.token
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
def delete_user(username: str, UserRequest: UserRequest):
    token = UserRequest.token
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

class SessionRequest(BaseModel):
    token: str = Depends(oauth2_scheme)

@app.get("/sessions", response_model=List[dict])
def list_sessions(SessionRequest: SessionRequest):
    token = SessionRequest.token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    sessions = list(sessions_db.find({"user_id": str(user["_id"])}, {"_id": 0}))
    return sessions

@app.get("/sessions/{session_id}", response_model=dict)
def get_session(session_id: str, SessionRequest: SessionRequest):
    token = SessionRequest.token
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
def delete_session(session_id: str, SessionRequest: SessionRequest):
    token = SessionRequest.token
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
    token: str = Depends(oauth2_scheme)

class QueryResponse(BaseModel):
    agent: str
    response: str

@app.post("/ask", response_model=QueryResponse)
def ask(query: QueryRequest):
    token = query.token
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