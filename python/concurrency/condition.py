import threading

MAX = 2
items = []
lock = threading.Lock()

space_available = threading.Condition(lock)   # producers wait on this
item_available  = threading.Condition(lock)   # consumers wait on this

def producer(i):
    with lock:
        while len(items) >= MAX:              # no space
            space_available.wait()            # wait until space is available
        items.append(i)
        item_available.notify()               # tell consumers: item is available

def consumer():
    with lock:
        while not items:                      # no item
            item_available.wait()             # wait until an item is available
        item = items.pop(0)
        space_available.notify()              # tell producers: space is available
        return item
