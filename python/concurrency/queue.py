import threading, queue, time

q = queue.Queue(maxsize=2)        # holds at most 2 items

def producer():
    for i in range(5):
        print(f"Trying to put {i}...")
        q.put(i)                  # BLOCKS here if the queue is full
        print(f"Put {i}")
    q.put(None)                   # signal: no more items

def consumer():
    while True:
        time.sleep(1)             # slow consumer, so the queue fills up
        item = q.get()            # frees a slot, unblocks the producer
        if item is None:
            break
        print(f"    Got {item}")

threading.Thread(target=producer).start()
threading.Thread(target=consumer).start()
