from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import sqlite3
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio
from src.mcpConnector import client

load_dotenv()
llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# binding llm to tools
# llm_with_tools=llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

async def build_graph():
    tools=await client.get_tools()
    print("Available tools:", tools)
    llm_with_tools=llm.bind_tools(tools)

    #nodes
    async def chat_node(state: ChatState):
        messages = state['messages']
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node=ToolNode(tools)

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")
    chatbot = graph.compile()

    return chatbot

async def main():
    chatbot=await build_graph()

    #running graph
    result=await chatbot.ainvoke({
        "messages":[HumanMessage(content="get all my expenses from dec 2025 to jan 2026") ]
    })
    print(result["messages"][-1].content)   

if __name__ == "__main__":
    asyncio.run(main())