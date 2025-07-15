from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langsmith import traceable
from app.classifier import AgentState
from app.crm_client import CRMClient
import os
import json
import ast

crm_client = CRMClient(api_key=os.environ.get("DIDAR_API_KEY"))

def list_users(requested_prompt: str) -> str:
    users = crm_client.list_users()
    return json.dumps({
        'data':users,
        'prompt':requested_prompt
    })

def list_product_categories(requested_prompt: str) -> str:
    categories = crm_client.list_product_categories()
    return json.dumps({
        'data':categories,
        'prompt':requested_prompt
    })

def list_products(requested_prompt: str) -> str:
    products = crm_client.list_products()
    return json.dumps({
        'data':products,
        'prompt':requested_prompt
    })

def format_json(json_input: str) -> str:
    prohibits = [
        "Id",
        "Code",
        "HasPicture",
        "PictureUrl",
        "InvitationUrl",
        "InvitationAccepted",
        "VisibilityId",
        "PermissionId",
        "Permissions",
        "UserId",
        "IsOwner",
        "IsDisabled",
        "DisplayName"
    ]

    try:
        parsed_input = json.loads(json_input)
        if isinstance(parsed_input, str):
            parsed_input = json.loads(parsed_input)
    except Exception:
        try:
            parsed_input = ast.literal_eval(json_input)
            if isinstance(parsed_input, str):
                parsed_input = ast.literal_eval(parsed_input)
        except Exception:
            return "Invalid JSON input."

    prompt = parsed_input.get("prompt", "")
    data = parsed_input.get("data", [])

    if isinstance(data, str):
        try:
            data = ast.literal_eval(data)
        except Exception:
            try:
                data = json.loads(data)
            except Exception:
                return "Invalid data field in input."

    output_lines = []
    if prompt:
        output_lines.append(f"User Prompt : {prompt}")
    else:
        output_lines.append("User Prompt not provided")

    if isinstance(data, list) and data:
        for item in data:
            if isinstance(item, dict):
                for k, v in item.items():
                    if k not in prohibits:
                        output_lines.append(f"- {k}: {v}")
                output_lines.append("")
            else:
                output_lines.append(f"- {str(item)}")
    elif isinstance(data, list):
        output_lines.append("(No data found)")
    else:
        output_lines.append("Data is not a list.")

    return "\n".join(output_lines).strip()


@traceable
def crm_agent_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    summerizer = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    chat_history = state.get("chat_history", [])

    summary_messages = [
        SystemMessage(content="You are a chat history summarizer. If there is no chat history, return nothing. Summarize this chat history:")
    ]

    for user, assistant in chat_history:
        summary_messages.append(HumanMessage(content=user))
        summary_messages.append(AIMessage(content=assistant))

    summary = summerizer.invoke(summary_messages)

    messages = [
        SystemMessage(
            content=(
                "You are an AI agent in a smart Chatbot API for an online shop, designed to handle customer relationship management (CRM) queries. "
                "You are the crm-agent, which means you are responsible for handling CRM-related questions. "
                "You have access to tools that connect to DIDAR CRM API, which allows you to search for users, get user details, and update user information. "
                "Don't try to answer questions that aren't related to shopping or customer relations or users. "
                "You are specified to answer only CRM related questions, strictly only answer CRM related questions."
                "Use the tool you have to fetch the content you need to answer the question, then format into a human-readable state. For example for lists, fetch the list, format the jsons and then show them as bullet point lists or tables."
                "Do not say things like 'I formatted the list' or summarize the output. Your final answer must directly include the full formatted result from the tool (i.e. everything in the observation), and nothing else. If the user's question involves listing (e.g. 'list', 'show all', 'get all users'), your response must be in the form of a bullet list or clear multi-item structure representing the full result — not a single summary or one-user focus. Avoid any explanatory phrases or conclusions — only output the formatted result."
                "Always include the full formatted data (excluding the informers like the 'User Prompt:' phrase from the beginning) from the tool in the final answer, and do not summarize or restate it."
                f"The chat history is summarized as follows: {summary.content}"
            )
        )
    ]

    list_users_tool = Tool(
        name="Fetch a List of Users",
        func=list_users,
        description="Fetchs a list of all users in the CRM system and returns them as a JSON that needs to be formatted."
    )

    list_product_categories_tool = Tool(
        name="Fetch a List of Product Categories",
        func=list_product_categories,
        description="Fetchs a list of all product categories in the CRM system and returns them as a JSON that needs to be formatted."
    )

    list_products_tool = Tool(
        name="Fetch a List of Products",
        func=list_products,
        description="Fetchs a list of all products in the CRM system and returns them as a JSON that needs to be formatted."
    )

    format_json_tool = Tool(
        name="Format JSON Data",
        func=format_json,
        description="Formats JSON Data into readable text that can be used as answer"
    )

    tools = [
        list_users_tool,
        list_products_tool,
        list_product_categories_tool,

        format_json_tool
    ]

    for user, assistant in chat_history:
        messages.append(HumanMessage(content=user))
        messages.append(AIMessage(content=assistant))

    messages.append(HumanMessage(content=state["question"]))

    agent = initialize_agent(
        tools,
        llm,
        verbose=True,
        handle_parsing_errors=True
    )

    response = agent.invoke({"input": state["question"]})["output"]

    if "chat_history" not in state:
        state["chat_history"] = []

    state["chat_history"].append((state["question"], response))

    return {
        **state,
        "answer": response
    }