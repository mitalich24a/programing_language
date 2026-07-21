from threading import Semaphore

class Foo:

    def __init__(self):
        self.s1 = Semaphore(0)
        self.s2 = Semaphore(0)

    def first(self, printFirst):
        printFirst()
        self.s1.release()

    def second(self, printSecond):
        self.s1.acquire()
        printSecond()
        self.s2.release()

    def third(self, printThird):
        self.s2.acquire()
        printThird()