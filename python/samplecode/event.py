from threading import Event

class Foo:

    def __init__(self):
        self.first_done = Event()
        self.second_done = Event()

    def first(self, printFirst):
        printFirst()
        self.first_done.set()

    def second(self, printSecond):
        self.first_done.wait()
        printSecond()
        self.second_done.set()

    def third(self, printThird):
        self.second_done.wait()
        printThird()