class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)       # call parent constructor
        self.breed = breed

class A: pass
class B(A): pass          # single
class C(B): pass          # multilevel
class D(A): pass          # hierarchical (B and D both from A)
class E(B, D): pass       # multiple
