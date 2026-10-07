class Animal:
    def speak(self): print("Sound")

class Dog(Animal):
    def speak(self): print("Bark")

class Cat(Animal):
    def speak(self): print("Meow")

for a in [Dog(), Cat()]:
    a.speak()


class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f"({self.x}, {self.y})"

print(Point(1, 2) + Point(3, 4))   # (4, 6)



def add(a, b, c=0):
    return a + b + c


magic methods

__init__	                            Constructor
__str__	                              print(obj) output
__repr__	                            Debug representation
__len__	                              len(obj)
__add__, __eq__, __lt__	              +, ==, <
__del__	                              Destructor
