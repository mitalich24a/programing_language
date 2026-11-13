
import time
import uuid
import threading

from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Callable, Any


# --------------------------------
# 1. Tool Definition
# --------------------------------

@dataclass
class Tool:
    name: str
    func: Callable
    description: str
    schema: dict[str, type]
    allowed_roles: set[str]


# --------------------------------
# 2. Tool Registry
# --------------------------------

class ToolRegistry:

    def __init__(self):
        self.tools = {}
        self.lock = threading.Lock()

    def register(self, tool: Tool):

        with self.lock:
            if tool.name in self.tools:
                raise ValueError("Tool already registered")

            self.tools[tool.name] = tool

    def get_tool(self, name):

        with self.lock:
            if name not in self.tools:
                raise ValueError("Tool not found")

            return self.tools[name]


# --------------------------------
# 3. Tool Executor
# --------------------------------

class ToolExecutor:

    def __init__(self, registry):
        self.registry = registry
        self.pool = ThreadPoolExecutor(max_workers=10)

        self.results = {}
        self.idempotency_lock = threading.Lock()

    def execute(
        self,
        name,
        user_role,
        execution_id=None,
        **kwargs
    ):

        tool = self.registry.get_tool(name)

        # Authorization
        if user_role not in tool.allowed_roles:
            raise PermissionError("Not authorized")

        # Input validation
        for key, expected_type in tool.schema.items():

            if key not in kwargs:
                raise ValueError(f"Missing argument: {key}")

            if type(kwargs[key]) is not expected_type:
                raise TypeError(f"Invalid type: {key}")

        if len(kwargs) != len(tool.schema):
            raise ValueError("Unexpected arguments")

        # Idempotency ID
        if execution_id is None:
            execution_id = str(uuid.uuid4())

        with self.idempotency_lock:
            if execution_id in self.results:
                return self.results[execution_id]

        # Retry with timeout
        for attempt in range(4):

            future = self.pool.submit(
                tool.func, **kwargs
            )

            try:
                result = future.result(timeout=30)

                with self.idempotency_lock:
                    self.results[execution_id] = result

                return result

            except TimeoutError:
                future.cancel()

            except Exception:
                pass

            if attempt == 3:
                raise RuntimeError("Tool failed after retries")

            time.sleep(2 ** attempt)

    def shutdown(self):
        self.pool.shutdown(wait=True)


# --------------------------------
# 4. Agent Orchestrator
# --------------------------------

class AgentOrchestrator:

    def __init__(self, executor):
        self.executor = executor

        self.events = {
            "search": threading.Event(),
            "account": threading.Event(),
            "risk": threading.Event()
        }

        self.results = {}
        self.errors = {}

        self.lock = threading.Lock()

    def run_tool(
        self,
        tool_name,
        event_name,
        user_role,
        dependencies=None,
        **kwargs
    ):

        try:

            # Wait for dependencies
            for dependency in dependencies or []:

                if not self.events[dependency].wait(timeout=30):
                    raise TimeoutError(
                        f"{dependency} timed out"
                    )

                with self.lock:
                    if dependency in self.errors:
                        raise RuntimeError(
                            f"{dependency} failed"
                        )

            # Execute tool
            execution_id = str(uuid.uuid4())

            result = self.executor.execute(
                tool_name,
                user_role,
                execution_id=execution_id,
                **kwargs
            )

            with self.lock:
                self.results[event_name] = result

        except Exception as e:

            with self.lock:
                self.errors[event_name] = str(e)

        finally:
            # Always wake dependent tasks
            self.events[event_name].set()

    def run(self):

        tasks = [
            (
                "search_customer",
                "search",
                [],
                {"customer_id": "C101"}
            ),
            (
                "fetch_account",
                "account",
                ["search"],
                {"customer_id": "C101"}
            ),
            (
                "check_risk",
                "risk",
                ["search"],
                {"customer_id": "C101"}
            )
        ]

        threads = []

        for tool_name, event_name, deps, kwargs in tasks:

            thread = threading.Thread(
                target=self.run_tool,
                kwargs={
                    "tool_name": tool_name,
                    "event_name": event_name,
                    "user_role": "banking_agent",
                    "dependencies": deps,
                    **kwargs
                }
            )

            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # Validate after parallel tasks finish
        if self.errors:
            raise RuntimeError(self.errors)

        print("Search:", self.results["search"])
        print("Account:", self.results["account"])
        print("Risk:", self.results["risk"])


# --------------------------------
# 5. Tool Functions
# --------------------------------

def search_customer(customer_id):
    print("Searching customer...")
    time.sleep(1)
    return {"customer_id": customer_id}


def fetch_account(customer_id):
    print("Fetching account...")
    time.sleep(1)
    return {"balance": 50000}


def check_risk(customer_id):
    print("Checking risk...")
    time.sleep(1)
    return {"risk": "LOW"}


# --------------------------------
# 6. Register Tools
# --------------------------------

registry = ToolRegistry()

registry.register(
    Tool(
        name="search_customer",
        func=search_customer,
        description="Find customer",
        schema={"customer_id": str},
        allowed_roles={"banking_agent", "admin"}
    )
)

registry.register(
    Tool(
        name="fetch_account",
        func=fetch_account,
        description="Fetch account details",
        schema={"customer_id": str},
        allowed_roles={"banking_agent", "admin"}
    )
)

registry.register(
    Tool(
        name="check_risk",
        func=check_risk,
        description="Check customer risk",
        schema={"customer_id": str},
        allowed_roles={"banking_agent", "admin"}
    )
)


# --------------------------------
# 7. Execute Agent Workflow
# --------------------------------

executor = ToolExecutor(registry)

orchestrator = AgentOrchestrator(executor)

try:
    orchestrator.run()
finally:
    executor.shutdown()
