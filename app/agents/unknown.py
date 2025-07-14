from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langsmith import traceable
from app.classifier import AgentState


@traceable
def unknown_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    summerizer = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    chat_history = state.get("chat_history", [])

    summary_messages = [
        SystemMessage(content="You are a chat history summarizer. Summarize this chat history:")
    ]

    for user, assistant in chat_history:
        summary_messages.append(HumanMessage(content=user))
        summary_messages.append(AIMessage(content=assistant))

    summary = summerizer.invoke(summary_messages)

    messages = [
        SystemMessage(
            content=(
                "You are an AI agent in a smart Chatbot API for an online shop, designed to handle customer relationship management (CRM) queries. "
                "You as an agent get invoked when other agents weren't available or they weren't related to the question asked by the user. In the other words, you are a CRM fallback assistant."
                "Don't try to answer questions that aren't related to shopping or customer relations or users. "
                "Prefer persian language for answering, but prioritize answering in the user's language. If user speaks in another language, try to answer in that language."
                f"The chat history is summarized as follows: {summary.content}"
            )
        )
    ]

    for user, assistant in chat_history:
        messages.append(HumanMessage(content=user))
        messages.append(AIMessage(content=assistant))

    messages.append(HumanMessage(content=state["question"]))
    response = llm(messages)

    if "chat_history" not in state:
        state["chat_history"] = []
    state["chat_history"].append((state["question"], response.content))

    return {
        **state,
        "answer": response.content
    }