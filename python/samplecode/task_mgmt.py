
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
    retry_count: int = 0
    max_retries: int = 3
    status: Status = Status.PENDING


class CircuitBreaker:

    def __init__(self, threshold=5, timeout=5):
        self.state = CBState.CLOSED
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure_time = 0
        self.lock = threading.Lock()

    def call(self, func):

        with self.lock:

            if self.state == CBState.OPEN:

                if time.time() - self.last_failure_time >= self.timeout:
                    self.state = CBState.HALF_OPEN
                else:
                    raise Exception("Circuit is OPEN")

            # Only one probe is allowed in HALF_OPEN
            elif self.state == CBState.HALF_OPEN:
                raise Exception("Probe already in progress")

        try:
            result = func()

            with self.lock:
                self.failure_count = 0
                self.state = CBState.CLOSED

            return result

        except Exception:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                self.state = CBState.OPEN

            raise


class Executor:

    def __init__(self, workers=3):
        self.q = queue.Queue()
        self.retry_pool = ThreadPoolExecutor(max_workers=1)
        self.breaker = CircuitBreaker()
        self.threads = []
        self.lock = threading.Lock()
        self.next_id = 1
        self.stopping = False

        for _ in range(workers):
            th = threading.Thread(target=self.run)
            th.start()
            self.threads.append(th)

    def add_task(self, name, func):

        with self.lock:
            task = Task(self.next_id, name, func)
            self.next_id += 1

        self.q.put(task)
        return task

    def run(self):

        while True:
            task = self.q.get()

            try:
                if task is None:
                    return

                task.status = Status.RUNNING

                try:
                    self.breaker.call(task.func)
                    task.status = Status.COMPLETED

                except Exception:

                    task.retry_count += 1

                    if task.retry_count <= task.max_retries:
                        task.status = Status.PENDING

                        delay = 2 ** (task.retry_count - 1)

                        self.retry_pool.submit(
                            self.retry_later, task, delay
                        )

                    else:
                        task.status = Status.FAILED

            finally:
                self.q.task_done()

    def retry_later(self, task, delay):

        time.sleep(delay)
        self.q.put(task)

    def shutdown(self):

        self.q.join()

        for _ in self.threads:
            self.q.put(None)

        for th in self.threads:
            th.join()

        self.retry_pool.shutdown(wait=True)


# Example

def task1():
    print("Executing task 1")
    return "Success"


def task2():
    print("Executing task 2")
    raise Exception("API failure")


ex = Executor(workers=3)

t1 = ex.add_task("Task 1", task1)
t2 = ex.add_task("Task 2", task2)

ex.shutdown()

print(t1.status)
print(t2.status)
