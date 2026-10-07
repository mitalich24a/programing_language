class CPU:
    def start(self): print("CPU started")

class Memory:
    def load(self): print("Memory loaded")

class Disk:
    def read(self): print("Disk read")

class Computer:                      # the facade
    def __init__(self):
        self.cpu, self.mem, self.disk = CPU(), Memory(), Disk()

    def boot(self):
        self.cpu.start()
        self.mem.load()
        self.disk.read()

Computer().boot()                    # one call instead of three
