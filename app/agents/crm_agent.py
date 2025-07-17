from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langsmith import traceable
from app.classifier import AgentState
from app.crm_client import CRMClient
import os
import json

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

def list_activity_types(requested_prompt: str) -> str:
    activites = crm_client.list_activity_types()
    return json.dumps({
        'data':activites,
        'prompt':requested_prompt
    })

def list_pipelines(requested_prompt: str) -> str:
    pipelines = crm_client.list_pipelines()
    return json.dumps({
        'data':pipelines,
        'prompt':requested_prompt
    })

def search_product(query: str) -> str:
    products = crm_client.search_product(query)
    return json.dumps({
        'data':products,
        'prompt':f"Search for product {query}"
    })

def search_attachment(query: str) -> str:
    attachments = crm_client.search_attachment(query)
    return json.dumps({
        'data':attachments,
        'prompt':f"Search for attachment {query}"
    })

def search_case(query: str) -> str:
    cases = crm_client.search_case(query)
    return json.dumps({
        'data':cases,
        'prompt':f"Search for case {query}"
    })

def search_deal(query: str) -> str:
    deals = crm_client.search_deal(query)
    return json.dumps({
        'data':deals,
        'prompt':f"Search for deal {query}"
    })

def search_company(query: str) -> str:
    companies = crm_client.search_company(query)
    return json.dumps({
        'data':companies,
        'prompt':f"Search for company {query}"
    })

def search_contact(query: str) -> str:
    contacts = crm_client.search_contact(query)
    return json.dumps({
        'data':contacts,
        'prompt':f"Search for contact {query}"
    })

def get_cards(ownerId: str) -> str:
    cards = crm_client.get_cards(ownerId)
    return json.dumps({
        'data':cards,
        'prompt':f"Get 10 last cards of the Owner with the ID of `{ownerId}`"
    })

def get_contact_detail(Id: str) -> str:
    details = crm_client.get_contact_detail(Id)
    return json.dumps({
        'data':details,
        'prompt':f"Get details of contact with the ID of `{Id}`"
    })

def get_deal_detail(Id: str) -> str:
    details = crm_client.get_deal_detail(Id)
    return json.dumps({
        'data':details,
        'prompt':f"Get details of a deal with the ID of `{Id}`"
    })

def format_json(json_input: str) -> str:
    formatter_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = (
        "You are a helpful assistant. Format the following JSON content into a readable list or table. "
        "Keep field names clear and values accurate. Do not summarize or skip items. "
        f"\n\nJSON Input:\n{json_input}"
    )

    return formatter_llm.invoke([HumanMessage(content=prompt)]).content


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
                "You are the crm-agent, responsible for handling only CRM-related questions. "
                "Your primary language is Persian, and you must respond in Persian when the user's input is in Persian. "
                "If the user speaks in a language other than Persian, respond in their language but include a polite message in that language stating: 'The system is optimized for Persian. For the best experience, please use Persian for your CRM-related questions.' "
                "For Persian inputs, do not include this message; respond only in Persian with the relevant CRM information. "
                "In Persian, use these terms: کاربر (users), کاریز (pipelines), مشتری (contacts), معامله (deal), محصول (product), فعالیت (activity), کارت (card). "
                "You have access to tools that connect to the DIDAR CRM API, allowing you to search for users, get user details, and update user information. "
                "Strictly answer only CRM-related questions. Do not respond to questions unrelated to shopping, customer relations, or users. "
                "When using tools to fetch data, format the output in a human-readable structure. For lists (e.g., 'list', 'show all', 'get all users'), present the full results as a bullet point list or table, including all data from the tool's observation without summarization. "
                "Do not include explanatory phrases like 'I formatted the list' or summarize the output. The final answer must consist only of the formatted result from the tool (e.g., the full list or data structure). "
                "If the user’s question involves listing, ensure the response is a clear multi-item structure (e.g., bullet points or table) representing the full result, not a single-item focus. "
                f"The chat history is summarized as follows: {summary.content}"
            )
        )
    ]

    list_users_tool = Tool(
        name="Fetch a List of Users",
        func=list_users,
        description="Fetchs a list of all users in the CRM system and returns them as a JSON that needs to be formatted. If the user was asking for a list, summerize the data."
    )

    list_product_categories_tool = Tool(
        name="Fetch a List of Product Categories",
        func=list_product_categories,
        description="Fetchs a list of all product categories in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer. If the user was asking for a list, summerize the data."
    )

    list_products_tool = Tool(
        name="Fetch a List of Products",
        func=list_products,
        description="Fetchs a list of all products in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer. If the user was asking for a list, summerize the data."
    )

    search_product_tool = Tool(
        name="Search for a Product",
        func=search_product,
        description="Takes a query to search in products in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer. "
    )

    search_attachment_tool = Tool(
        name="Search for an attachment",
        func=search_attachment,
        description="Takes a query to search in attachments in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer"
    )

    search_case_tool = Tool(
        name="Search for a case",
        func=search_case,
        description="Takes a query to search in attachments in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer"
    )

    search_company_tool = Tool(
        name="Search for a company",
        func=search_company,
        description="Takes a query to search in companies in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer"
    )

    search_contact_tool = Tool(
        name="Search for a Contact",
        func=search_contact,
        description="Takes a query to search in contacts in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer"
    )

    search_deal_tool = Tool(
        name="Search for a Deal",
        func=search_deal,
        description="Takes a query to search in deals in the CRM system and returns them as a JSON that needs to be formatted then can be used as an answer"
    )

    get_cards_tool = Tool(
        name="Fetch a list of an Owner's Cards",
        func=get_cards,
        description="Takes an `OwnerID` which could be obtained through fetching a list of the owners by using the `Fetch a List of users` Tool and check if they are owner, then you can grab their Id to pass to this tool. This tool lists the details of the cards of that owner. This tool returns the list as a JSON that needs to be formatted then can be used as an answer"
    )

    get_contact_detail_tool = Tool(
        name="Get a Contact's Details",
        func=get_contact_detail,
        description="Takes a `ContactId` which could be obtained through search for a contact using the `Search for a contact` tool and grabbing their ID to pass to this tool. This tool lists the details of the contact. This tool returns the list as a JSON that needs to be formatted then can be used as an answer"
    )

    get_deal_detail_tool = Tool(
        name="Get a deal's Details",
        func=get_deal_detail,
        description="Takes a `DealId` which could be obtained through search for a deal using the `Search for a Deal` tool and grabbing their ID to pass to this tool. This tool lists the details of the deal. This tool returns the list as a JSON that needs to be formatted then can be used as an answer"
    )

    format_json_tool = Tool(
        name="Format JSON Data",
        func=format_json,
        description="Formats JSON data using an LLM into readable and understandable text or list."
    )

    tools = [
        list_users_tool,
        list_products_tool,
        list_product_categories_tool,
        search_product_tool,
        search_attachment_tool,
        search_case_tool,
        search_company_tool,
        search_contact_tool,
        search_deal_tool,
        get_cards_tool,
        get_contact_detail_tool,
        get_deal_detail_tool,
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