from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.agent import graph
from app.auth import create_access_token, verify_token, users_db
from dotenv import load_dotenv

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/signin")

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
    users_db.insert_one({"username": form_data.username, "password": form_data.password})
    return {"message": "User created successfully"}

@app.post("/signin")
def signin(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.find_one({"username": form_data.username})
    if not user or user["password"] != form_data.password:
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
    

class QueryRequest(BaseModel):
    query: str
    token: str = Depends(oauth2_scheme)

class QueryResponse(BaseModel):
    agent: str
    response: str

@app.post("/ask", response_model=QueryResponse)
def ask(query: QueryRequest):
    token = query.token
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        username = verify_token(token)
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    if not query.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    state = {"question": query.query}
    result = graph.invoke(state)
    return QueryResponse(
        agent = result["agent"],
        response = result.get("answer", "No answer provided")
    )