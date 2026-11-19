
from langchain_core.messages import HumanMessage


class AgentHarness:

    def __init__(self, graph, max_steps=12):

        self.graph = graph
        self.max_steps = max_steps

    async def run(
        self,
        tenant_id,
        user_id,
        conversation_id,
        query
    ):

        if not query or len(query) > 4000:
            raise ValueError("Invalid query")

        # Scope the thread to authenticated identity
        thread_id = (
            f"{tenant_id}:{user_id}:{conversation_id}"
        )

        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "recursion_limit": self.max_steps
        }

        # Invoke the graph
        result = await self.graph.ainvoke(
            {
                "messages": [
                    HumanMessage(content=query)
                ]
            },
            config=config
        )

        # Get the final message
        final_message = result["messages"][-1]

        return final_message.content
