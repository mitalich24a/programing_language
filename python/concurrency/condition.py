import threading, time

MAX = 2
items = []
cond = threading.Condition()

def producer():
    for i in range(5):
        with cond:
            while len(items) >= MAX:      # while FULL, wait
                print(f"Full, producer waiting before {i}...")
                cond.wait()               # releases lock and sleeps
            items.append(i)
            print(f"Produced {i}  {items}")
            cond.notify()                 # wake the consumer

def consumer():
    for _ in range(5):
        time.sleep(1)                     # slow consumer
        with cond:
            while not items:              # while EMPTY, wait
                cond.wait()
            item = items.pop(0)
            print(f"    Consumed {item}  {items}")
            cond.notify()                 # wake the producer (space is free)

threading.Thread(target=producer).start()
threading.Thread(target=consumer).start()
