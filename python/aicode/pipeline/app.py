
import asyncio

from pathlib import Path

from langchain.mcp import MCPAdapter

from agent.graph import build_graph
from agent.harness import AgentHarness


async def main():

    # Connect to the MCP server
    server_path = Path("mcp_server.py").resolve()

    async with MCPAdapter(server_path) as adapter:

        # Discover tools from MCP server
        mcp_tools = await adapter.list_tools()

        print("Discovered MCP tools:")

        for tool in mcp_tools:
            print(tool.name)

        # Build LangGraph
        graph = build_graph(mcp_tools)

        # Initialize Agent Harness
        harness = AgentHarness(
            graph=graph,
            max_steps=12
        )

        print("\nBanking AI Agent is ready.")

        while True:

            query = input("\nYou: ")

            if query.lower() in ["exit", "quit"]:
                break

            try:

                answer = await harness.run(
                    tenant_id="retail",
                    user_id="U101",
                    conversation_id="SESSION101",
                    query=query
                )

                print("\nAgent:", answer)

            except Exception as error:

                print("\nAgent error:", str(error))


if __name__ == "__main__":
    asyncio.run(main())
