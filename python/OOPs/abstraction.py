from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self): pass

class Square(Shape):
    def __init__(self, s): self.s = s
    def area(self): return self.s ** 2
