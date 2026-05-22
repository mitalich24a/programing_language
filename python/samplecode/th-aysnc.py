
import threading
import time


def foo():
	print("Foo Thread", threading.current_thread().name)
	print("Hello World")
	time.sleep(10)

def test():
	th = threading.Thread(target=foo)
	th.start()


print("Main Thread", threading.current_thread().name)
test()
print("Main Thread Exiting", threading.current_thread().name)



################################################################

import asyncio
import threading
import time

async def foo(a):
	print("Foo Thread", a, threading.current_thread().name)
	print("Hello World", a)
	time.sleep(5)
	print("Foo Thread", a, threading.current_thread().name)
	print("Good Bye World", a)

async def main():
	await asyncio.gather(foo(1), foo(2))

asyncio.run(main())


################################################################


import asyncio
import threading
import time

async def foo(a):
	print("Hello World", a, threading.current_thread().name)
	await asyncio.sleep(5)
	print("Good Bye World", a, threading.current_thread().name)

async def main():
	await asyncio.gather(foo(1), foo(2))

asyncio.run(main())

