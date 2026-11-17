
import asyncio
from pathlib import Path

from fastmcp import Client
from langchain.mcp import MCPAdapter
from langchain.agents import create_agent
from langchain_ollama import ChatOllama


async def main():

    # 1. Initialize Ollama
    llm = ChatOllama(
        model="llama3.1",
        temperature=0
    )

    # 2. Connect to MCP server
    server_path = Path(__file__).parent / "banking_server.py"

    async with MCPAdapter(server_path) as adapter:

        # 3. Discover available tools
        tools = await adapter.list_tools()

        print("Discovered tools:")
        for tool in tools:
            print(tool.name)

        # 4. Create LangGraph agent
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are a banking assistant. "
                "Use available tools to answer "
                "account balance and transaction queries. "
                "Never invent account information."
            )
        )

        # 5. Execute user request
        response = await agent.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": "What is the balance of ACC101?"
                }
            ]
        })

        # 6. Display response
        print("\nAgent response:")
        print(response["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
