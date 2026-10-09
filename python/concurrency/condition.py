import threading

MAX = 2
items = []
lock = threading.Lock()

space_available = threading.Condition(lock)
item_available = threading.Condition(lock)

def producer(i):
    with space_available:
        while len(items) >= MAX:
            space_available.wait()

        items.append(i)
        print(f"Added {i}")

        item_available.notify()

def consumer():
    with item_available:
        while not items:
            item_available.wait()

        item = items.pop(0)
        print(f"Removed {item}")

        space_available.notify()
        return item
