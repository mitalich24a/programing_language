import threading, time

sem = threading.Semaphore(3)     # max 3 threads inside at once

def download(n):
    with sem:
        print(f"Task {n} started")
        time.sleep(1)
        print(f"Task {n} done")

for i in range(6):
    threading.Thread(target=download, args=(i,)).start()
  
# Only 3 run together; the other 3 wait for a free permit
