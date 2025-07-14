# 🛒 CRM Chatbot API for Online Shop

This project implements an **AI-powered chatbot API** for customer relationship management (CRM) in an online shop, seamlessly integrated with [Didar CRM](https://didar.me/). It leverages advanced language model orchestration with **LangChain** and **LangGraph**, includes robust **LangSmith** tracing for monitoring agent behavior, and uses **FastAPI** for a high-performance web API layer. The project is fully containerized with **Docker** and supports **on-demand testing via GitHub Actions**.

---

## 🚀 Features

- 🤖 **AI Agent for CRM**: Handles customer queries, FAQs, orders, follow-ups, and more using a LangGraph-based agent.
- 🧠 **LangChain + LangGraph**: Modular, stateful agent architecture powered by modern LLM routing and tools.
- 📊 **LangSmith Monitoring**: Full traceability and observability for debugging and performance analysis.
- 🔌 **Didar CRM Integration**: Easily connects to the Didar CRM API to access and update customer data.
- 🌐 **FastAPI Backend**: High-speed, production-ready REST API.
- 🐳 **Dockerized**: Runs consistently across environments using Docker.
- ✅ **CI/CD with GitHub Workflows**: On-demand test suite using Pytest and GitHub Actions.

---

## 🧱 Tech Stack

| Component      | Tech                             |
|----------------|----------------------------------|
| Programming    | Python                           |
| Web Framework  | [FastAPI](https://fastapi.tiangolo.com) |
| AI Agent       | [LangChain](https://www.langchain.com/) + [LangGraph](https://www.langchain.com/langgraph) |
| Monitoring     | [LangSmith](https://smith.langchain.com) |
| CRM Platform   | [Didar.me](https://didar.me/)    |
| Containerization | Docker                         |
| CI/CD          | GitHub Actions                   |

---

## 📂 Project Structure

```
.
├── app/
│   ├── main.py           # FastAPI app entrypoint
│   ├── agent.py          # LangGraph agent implementation
│   ├── auth.py           # Authorization Process
│   ├── crm_client.py     # Integration with Didar CRM API
│   ├── classifier.py     # Topic classification logic
│   ├── agents/
│   │   ├── crm_agent.py  # Specialized bot for CRM queries
│   │   ├── unknown.py
├── tests/                # Pytest test cases
│   │   ...
├── Dockerfile            # Docker image definition
├── .github/workflows
│   │   ├── ci.yml
├── README.md
```

---

## 🛠️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/BMDarkLight/crm-chatbot-api.git
cd crm-chatbot-api
```

### 2. Setup Environment Variable File

Use **.env.example** file provided in the repository to curate your own **.env** file and put it in root directory of the project.

### 3. Run Locally with Docker

```bash
docker build -t crm-chatbot-api .
docker run -p 8000:8000 --env-file .env crm-chatbot-api
```

API will be available at port 8000 using default settings for docker container

You can also pull the lastest build of repository's docker image:

```bash
docker pull bmdarklight/crm-chatbot-api
```

https://hub.docker.com/repository/docker/bmdarklight/crm-chatbot-api/general

---


## 🧪 Run Tests

Tests are written with Pytest and executed automatically via GitHub Actions.

To run locally:

```bash
pytest
```
