import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():

    # Connect to already-running MCP server
    async with streamable_http_client(
        "https://mcp.company.com/mcp"
    ) as (read, write, _):

        async with ClientSession(read, write) as session:

            # Handshake
            await session.initialize()

            # Discover tools
            tools = await session.list_tools()

            print(tools.tools)

            # Execute tool
            result = await session.call_tool(
                "get_employee",
                {
                    "employee_id": "123"
                }
            )

            print(result.content[0].text)


asyncio.run(main())
