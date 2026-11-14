
import threading
import queue
import time
from dataclasses import dataclass, field
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
    kwargs: dict = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    status: Status = Status.PENDING
    result: object = None
    error: object = None


class CircuitBreaker:

    def __init__(self, threshold=5, timeout=5):
        self.state = CBState.CLOSED
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure_time = 0
        self.probe_in_progress = False
        self.lock = threading.Lock()

    def call(self, func):

        is_probe = False

        with self.lock:

            if self.state == CBState.OPEN:

                if time.time() - self.last_failure_time < self.timeout:
                    raise Exception("Circuit is OPEN")

                self.state = CBState.HALF_OPEN
                self.probe_in_progress = True
                is_probe = True

            elif self.state == CBState.HALF_OPEN:
                raise Exception("Probe already in progress")

        try:
            result = func()

            with self.lock:
                if is_probe:
                    self.state = CBState.CLOSED
                    self.failure_count = 0
                    self.probe_in_progress = False
                elif self.state == CBState.CLOSED:
                    self.failure_count = 0

            return result

        except Exception:

            with self.lock:

                if is_probe:
                    self.state = CBState.OPEN
                    self.last_failure_time = time.time()
                    self.probe_in_progress = False

                elif self.state == CBState.CLOSED:
                    self.failure_count += 1

                    if self.failure_count >= self.threshold:
                        self.state = CBState.OPEN
                        self.last_failure_time = time.time()

            raise


class Executor:

    def __init__(self, workers=3):

        self.q = queue.Queue()
        self.retry_pool = ThreadPoolExecutor(max_workers=1)
        self.breaker = CircuitBreaker()

        self.threads = []
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

        self.next_id = 1
        self.pending_tasks = 0
        self.accepting_tasks = True

        for _ in range(workers):
            th = threading.Thread(target=self.run)
            th.start()
            self.threads.append(th)

    def add_task(self, name, func, *args, max_retries=3, **kwargs):

        with self.condition:

            if not self.accepting_tasks:
                raise RuntimeError("Executor is shutting down")

            task = Task(
                id=self.next_id,
                name=name,
                func=func,
                args=args,
                kwargs=kwargs,
                max_retries=max_retries
            )

            self.next_id += 1
            self.pending_tasks += 1

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

            task.result = self.breaker.call(
                lambda: task.func(*task.args, **task.kwargs)
            )

            task.status = Status.COMPLETED
            print(f"Task {task.id} completed")

            self.finish_task()

        except Exception as e:

            task.error = e
            task.retry_count += 1

            print(
                f"Task {task.id} failed: {e}. "
                f"Attempt {task.retry_count}"
            )

            if task.retry_count <= task.max_retries:

                task.status = Status.PENDING

                delay = 2 ** (task.retry_count - 1)

                print(f"Retrying task {task.id} after {delay} seconds")

                try:
                    self.retry_pool.submit(
                        self.retry_later,
                        task,
                        delay
                    )

                except RuntimeError as submit_error:
                    task.status = Status.FAILED
                    task.error = submit_error
                    self.finish_task()

            else:
                task.status = Status.FAILED
                print(f"Task {task.id} permanently failed")
                self.finish_task()

    def retry_later(self, task, delay):

        time.sleep(delay)
        self.q.put(task)

    def finish_task(self):

        with self.condition:
            self.pending_tasks -= 1
            self.condition.notify_all()

    def shutdown(self):

        with self.condition:

            self.accepting_tasks = False

            while self.pending_tasks > 0:
                self.condition.wait()

        for _ in self.threads:
            self.q.put(None)

        for th in self.threads:
            th.join()

        self.retry_pool.shutdown(wait=True)

        print("Executor shutdown complete")


# -------------------------
# Example functions
# -------------------------

def add(a, b):
    print(f"Adding {a} + {b}")
    return a + b


def api_call(name, attempt):

    print(f"Calling API: {name}, attempt: {attempt}")

    if attempt < 3:
        raise Exception("API failure")

    return f"Success: {name}"


def failing_task():
    print("Executing failing task")
    raise Exception("Something went wrong")


# -------------------------
# Main
# -------------------------

if __name__ == "__main__":

    ex = Executor(workers=3)

    t1 = ex.add_task("Addition", add, 10, 20)

    t2 = ex.add_task(
        "API Task",
        api_call,
        "OpenAI",
        3
    )

    t3 = ex.add_task(
        "Failing Task",
        failing_task,
        max_retries=3
    )

    ex.shutdown()

    print("\nFinal Results")

    for task in [t1, t2, t3]:

        print(
            task.id,
            task.name,
            task.status.value,
            task.result,
            task.retry_count
        )
