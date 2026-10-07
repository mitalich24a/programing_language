import threading

count = 0
lock = threading.Lock()

def add():
    global count
    for _ in range(100000):
        with lock:          # acquire, run, release automatically
            count += 1

t1 = threading.Thread(target=add)
t2 = threading.Thread(target=add)
t1.start(); t2.start()
t1.join(); t2.join()

print(count)    # always 200000
