import threading

count = 0

def add():
    global count
    for _ in range(100000):
        count += 1          # read, add, write (3 steps, not atomic)

t1 = threading.Thread(target=add)
t2 = threading.Thread(target=add)
t1.start(); t2.start()
t1.join(); t2.join()

print(count)    # expected 200000, often less
