
import threading
import queue
import time
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor


class Status(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CBState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class Task:
    id: int
    name: str
    func: object
    args: tuple = ()
    kwargs: dict = None
    retry_count: int = 0
    max_retries: int = 3
    status: Status = Status.PENDING


class CircuitBreaker:

    def __init__(self, threshold=5, timeout=5):
        self.state = CBState.CLOSED
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = 0
        self.probe = False
        self.lock = threading.Lock()

    def call(self, func):

        with self.lock:

            if self.state == CBState.OPEN:
                if time.time() - self.last_failure < self.timeout:
                    raise Exception("Circuit OPEN")

                self.state = CBState.HALF_OPEN
                self.probe = True

            elif self.state == CBState.HALF_OPEN:
                raise Exception("Probe in progress")

        try:
            result = func()

            with self.lock:
                self.state = CBState.CLOSED
                self.failures = 0
                self.probe = False

            return result

        except Exception:

            with self.lock:
                self.failures += 1
                self.last_failure = time.time()

                if self.failures >= self.threshold or self.state == CBState.HALF_OPEN:
                    self.state = CBState.OPEN

                self.probe = False

            raise


class Executor:

    def __init__(self, workers=3):

        self.q = queue.Queue()
        self.retry_pool = ThreadPoolExecutor(max_workers=1)
        self.breaker = CircuitBreaker()

        self.threads = []
        self.next_id = 1

        self.pending = 0
        self.lock = threading.Lock()
        self.accepting = True

        for _ in range(workers):
            t = threading.Thread(target=self.run)
            t.start()
            self.threads.append(t)

    def add_task(self, name, func, *args, **kwargs):

        with self.lock:
            if not self.accepting:
                raise RuntimeError("Executor stopped")

            task = Task(
                self.next_id,
                name,
                func,
                args,
                kwargs
            )

            self.next_id += 1
            self.pending += 1

        self.q.put(task)
        return task

    def run(self):

        while True:
            task = self.q.get()

            try:
                if task is None:
                    return

                self.execute(task)

            finally:
                self.q.task_done()

    def execute(self, task):

        task.status = Status.RUNNING

        try:
            self.breaker.call(
                lambda: task.func(*task.args, **task.kwargs)
            )

            task.status = Status.COMPLETED
            print(task.name, "COMPLETED")

            self.finish()

        except Exception as e:

            task.retry_count += 1
            print(task.name, "FAILED:", e)

            if task.retry_count <= task.max_retries:

                task.status = Status.PENDING

                delay = 2 ** (task.retry_count - 1)

                self.retry_pool.submit(
                    self.retry_later,
                    task,
                    delay
                )

            else:
                task.status = Status.FAILED
                self.finish()

    def retry_later(self, task, delay):

        time.sleep(delay)
        self.q.put(task)

    def finish(self):

        with self.lock:
            self.pending -= 1

    def shutdown(self):

        with self.lock:
            self.accepting = False

        # Wait until all tasks and retries finish.
        while True:
            with self.lock:
                if self.pending == 0:
                    break
            time.sleep(0.1)

        for _ in self.threads:
            self.q.put(None)

        for t in self.threads:
            t.join()

        self.retry_pool.shutdown(wait=True)

        print("Shutdown complete")


# -------------------------
# Example
# -------------------------

def add(a, b):
    print("Adding:", a, b)
    return a + b


def api_call(name, attempt):

    print("Calling API:", name, attempt)

    if attempt < 3:
        raise Exception("API failure")

    return "Success"


def failing_task():
    raise Exception("Always fails")


# -------------------------
# Main
# -------------------------

if __name__ == "__main__":

    ex = Executor(workers=3)

    t1 = ex.add_task("Addition", add, 10, 20)

    t2 = ex.add_task(
        "API",
        api_call,
        "OpenAI",
        3
    )

    t3 = ex.add_task(
        "Failing",
        failing_task
    )

    ex.shutdown()

    print("\nFinal Status")

    for t in [t1, t2, t3]:
        print(t.name, t.status.value, t.retry_count)
