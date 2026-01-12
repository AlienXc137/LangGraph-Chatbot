from langchain_mcp_adapters.client import MultiServerMCPClient

#mcp client setup (fastmcp)
client=MultiServerMCPClient({
    "calculator": {
        "transport" : "stdio",
        "command" : "python",
        "args": ["C:\\Azhar\\LangGraph Chatbot\\src\\mcp-clients\\calculator_mcp.py"]
    },
    "expense": {
        "transport":"streamable_http",
        "url": "https://marvelsaz-mcp.fastmcp.app/mcp"
    }
})
