
import json
import os
import time
import uuid
import threading

from concurrent.futures import ThreadPoolExecutor, wait
from typing import Callable

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage,
    message_to_dict,
    messages_from_dict,
)


# ==================================================
# 1. PERSISTENT STORAGE
# ==================================================

class Storage:

    def __init__(self, filename="agent_data.json"):
        self.filename = filename
        self.lock = threading.RLock()

        if not os.path.exists(filename):
            self.data = {
                "memories": {},
                "checkpoints": {}
            }
            self._save()
        else:
            with open(filename, "r") as file:
                self.data = json.load(file)

    def _save(self):
        temp = self.filename + ".tmp"

        with open(temp, "w") as file:
            json.dump(self.data, file, indent=2)

        os.replace(temp, self.filename)

    def save_preference(self, user_id, key, value):
        with self.lock:
            memory = self.data["memories"].setdefault(
                user_id,
                {"semantic": {}, "episodic": []}
            )

            memory["semantic"][key] = value
            self._save()

    def get_preferences(self, user_id):
        with self.lock:
            return self.data["memories"].get(
                user_id,
                {"semantic": {}, "episodic": []}
            )["semantic"].copy()

    def add_event(self, user_id, event):
        with self.lock:
            memory = self.data["memories"].setdefault(
                user_id,
                {"semantic": {}, "episodic": []}
            )

            memory["episodic"].append(event)
            self._save()

    def save_checkpoint(self, thread_id, user_id, messages, status):
        with self.lock:
            self.data["checkpoints"][thread_id] = {
                "user_id": user_id,
                "messages": [
                    message_to_dict(message)
                    for message in messages
                ],
                "status": status
            }
            self._save()

    def get_checkpoint(self, thread_id, user_id):
        with self.lock:
            checkpoint = self.data["checkpoints"].get(thread_id)

            if checkpoint is None:
                return None

            if checkpoint["user_id"] != user_id:
                raise PermissionError("Thread access denied")

            return checkpoint.copy()


# ==================================================
# 2. TOOL REGISTRY
# ==================================================

class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name, func):
        if name in self.tools:
            raise ValueError("Tool already registered")

        self.tools[name] = func

    def discover(self):
        return list(self.tools.keys())

    def execute(self, name, arguments):

        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        return self.tools[name].invoke(arguments)


# ==================================================
# 3. BANKING TOOLS
# ==================================================

ACCOUNTS = {
    "ACC101": {
        "balance": 50000,
        "currency": "INR"
    },
    "ACC102": {
        "balance": 25000,
        "currency": "INR"
    }
}


@tool
def get_balance(account_id: str) -> dict:
    """Get the current balance of a bank account."""

    account = ACCOUNTS.get(account_id)

    if not account:
        raise ValueError("Account not found")

    return {
        "account_id": account_id,
        "balance": account["balance"],
        "currency": account["currency"]
    }


@tool
def get_transactions(account_id: str) -> list:
    """Get recent transactions of a bank account."""

    if account_id not in ACCOUNTS:
        raise ValueError("Account not found")

    return [
        {"type": "CREDIT", "amount": 10000},
        {"type": "DEBIT", "amount": 2000}
    ]


# ==================================================
# 4. MEMORY TOOL
# ==================================================

def build_registry(storage, user_id):

    registry = ToolRegistry()

    registry.register("get_balance", get_balance)
    registry.register("get_transactions", get_transactions)

    # Bind authenticated user ID in application code.
    # Do not allow the LLM to choose another user's ID.

    @tool
    def remember_preference(key: str, value: str) -> str:
        """Save a customer's preference for future conversations."""

        storage.save_preference(user_id, key, value)

        return f"Saved preference: {key}"

    registry.register(
        "remember_preference",
        remember_preference
    )

    return registry


# ==================================================
# 5. TOOL EXECUTION WITH RETRIES
# ==================================================

def execute_with_retry(registry, name, arguments, retries=2):

    for attempt in range(retries + 1):

        try:
            return {
                "success": True,
                "result": registry.execute(name, arguments)
            }

        except ValueError as error:
            # Validation errors are not retried.
            return {
                "success": False,
                "error": str(error)
            }

        except Exception as error:

            if attempt == retries:
                return {
                    "success": False,
                    "error": str(error)
                }

            time.sleep(2 ** attempt)


# ==================================================
# 6. PARALLEL TOOL EXECUTION
# ==================================================

def execute_tool_calls(registry, calls, timeout=10):

    results = [None] * len(calls)

    executor = ThreadPoolExecutor(
        max_workers=min(4, len(calls))
    )

    futures = {}

    for index, call in enumerate(calls):

        future = executor.submit(
            execute_with_retry,
            registry,
            call["name"],
            call["args"]
        )

        futures[future] = index

    completed, pending = wait(
        futures,
        timeout=timeout
    )

    for future in completed:
        index = futures[future]

        try:
            results[index] = future.result()

        except Exception as error:
            results[index] = {
                "success": False,
                "error": str(error)
            }

    for future in pending:
        index = futures[future]

        future.cancel()

        results[index] = {
            "success": False,
            "error": "Tool execution timed out"
        }

    executor.shutdown(
        wait=False,
        cancel_futures=True
    )

    return results


# ==================================================
# 7. AGENT EXECUTION ENGINE
# ==================================================

class Agent:

    def __init__(self, storage, user_id):

        self.storage = storage
        self.user_id = user_id

        self.registry = build_registry(
            storage,
            user_id
        )

        self.llm = ChatOllama(
            model="llama3.1",
            temperature=0
        )

        self.llm_with_tools = self.llm.bind_tools(
            list(self.registry.tools.values())
        )

    def create_messages(self, preferences):

        system_prompt = """
        You are a banking assistant.

        Available tools allow you to:
        1. Check account balance.
        2. Fetch transactions.
        3. Save customer preferences.

        Use tools when necessary.
        Never invent banking information.
        Never claim an operation succeeded unless confirmed.
        """

        system_prompt += (
            "\nCustomer preferences: "
            + json.dumps(preferences)
        )

        return [SystemMessage(content=system_prompt)]

    def run_loop(self, thread_id, messages, max_steps=8):

        for step in range(max_steps):

            # Save execution checkpoint
            self.storage.save_checkpoint(
                thread_id,
                self.user_id,
                messages,
                "RUNNING"
            )

            # Ask LLM
            response = self.llm_with_tools.invoke(messages)

            messages.append(response)

            # Save LLM response
            self.storage.save_checkpoint(
                thread_id,
                self.user_id,
                messages,
                "RUNNING"
            )

            # No tool calls: final answer
            if not response.tool_calls:

                self.storage.save_checkpoint(
                    thread_id,
                    self.user_id,
                    messages,
                    "COMPLETED"
                )

                self.storage.add_event(
                    self.user_id,
                    {
                        "event": "conversation_completed",
                        "timestamp": time.time()
                    }
                )

                return response.content

            # Execute requested tools
            calls = response.tool_calls

            results = execute_tool_calls(
                self.registry,
                calls
            )

            # Return tool results to LLM
            for call, result in zip(calls, results):

                messages.append(
                    ToolMessage(
                        content=json.dumps(result, default=str),
                        tool_call_id=call["id"],
                        name=call["name"]
                    )
                )

            self.storage.save_checkpoint(
                thread_id,
                self.user_id,
                messages,
                "RUNNING"
            )

        self.storage.save_checkpoint(
            thread_id,
            self.user_id,
            messages,
            "MAX_STEPS_REACHED"
        )

        return "Agent stopped: maximum execution steps reached."

    def run(self, thread_id, query):

        preferences = self.storage.get_preferences(
            self.user_id
        )

        checkpoint = self.storage.get_checkpoint(
            thread_id,
            self.user_id
        )

        if checkpoint:
            messages = messages_from_dict(
                checkpoint["messages"]
            )
        else:
            messages = self.create_messages(preferences)

        # Add new user request
        messages.append(HumanMessage(content=query))

        return self.run_loop(thread_id, messages)

    def resume(self, thread_id):

        checkpoint = self.storage.get_checkpoint(
            thread_id,
            self.user_id
        )

        if not checkpoint:
            return "No checkpoint found."

        if checkpoint["status"] != "RUNNING":
            return "No interrupted execution to resume."

        messages = messages_from_dict(
            checkpoint["messages"]
        )

        return self.run_loop(thread_id, messages)


# ==================================================
# 8. APPLICATION
# ==================================================

if __name__ == "__main__":

    storage = Storage()

    # In a real application, get this from authenticated identity.
    user_id = "USER101"

    thread_id = str(uuid.uuid4())

    agent = Agent(storage, user_id)

    print("Banking Agent Started")
    print("Thread:", thread_id)

    while True:

        query = input("\nYou: ")

        if query.lower() == "exit":
            break

        if query.lower() == "resume":
            response = agent.resume(thread_id)
        else:
            response = agent.run(thread_id, query)

        print("\nAgent:", response)
