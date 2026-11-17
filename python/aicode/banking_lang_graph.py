
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command
from langchain_ollama import ChatOllama

import sqlite3


# 1. LLM
llm = ChatOllama(
    model="llama3.1",
    temperature=0
)


# 2. Shared state
class AgentState(TypedDict):
    customer_id: str
    amount: float
    balance: float
    approved: Optional[bool]
    status: str


# 3. Nodes

def check_balance(state: AgentState):
    print("Checking balance...")

    # Simulated database lookup
    balance = 50000

    return {"balance": balance}


def validate_transfer(state: AgentState):
    print("Validating transfer...")

    if state["amount"] <= 0:
        return {"status": "INVALID_AMOUNT"}

    if state["amount"] > state["balance"]:
        return {"status": "INSUFFICIENT_FUNDS"}

    return {"status": "READY_FOR_APPROVAL"}


def approval_node(state: AgentState):
    decision = interrupt({
        "message": "Approve this transfer?",
        "amount": state["amount"],
        "customer_id": state["customer_id"]
    })

    return {"approved": decision}


def execute_transfer(state: AgentState):
    if state["approved"]:
        return {"status": "TRANSFER_COMPLETED"}

    return {"status": "TRANSFER_REJECTED"}


# 4. Conditional routing

def route_after_validation(state: AgentState):
    if state["status"] == "READY_FOR_APPROVAL":
        return "approval"

    return "end"


def route_after_approval(state: AgentState):
    if state["approved"]:
        return "execute"

    return "end"


# 5. Build graph
graph = StateGraph(AgentState)

graph.add_node("check_balance", check_balance)
graph.add_node("validate", validate_transfer)
graph.add_node("approval", approval_node)
graph.add_node("execute", execute_transfer)

graph.add_edge(START, "check_balance")
graph.add_edge("check_balance", "validate")

graph.add_conditional_edges(
    "validate",
    route_after_validation,
    {
        "approval": "approval",
        "end": END
    }
)

graph.add_conditional_edges(
    "approval",
    route_after_approval,
    {
        "execute": "execute",
        "end": END
    }
)

graph.add_edge("execute", END)


# 6. SQLite checkpointing

connection = sqlite3.connect(
    "bank_agent.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)

app = graph.compile(checkpointer=checkpointer)


# 7. Execute graph

config = {
    "configurable": {
        "thread_id": "customer-101"
    }
}

initial_state = {
    "customer_id": "customer-101",
    "amount": 10000,
    "balance": 0,
    "approved": None,
    "status": "STARTED"
}

result = app.invoke(initial_state, config=config)

print("Execution paused:", result)


# 8. Resume after approval

result = app.invoke(
    Command(resume=True),
    config=config
)

print("Final result:", result)
