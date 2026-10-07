class Student:
    def __init__(self, name, age):   # constructor
        self.name = name             # instance variable
        self.age = age

    def show(self):
        print(self.name, self.age)

s = Student("Ravi", 20)   # object
s.show()                  # Ravi 20
