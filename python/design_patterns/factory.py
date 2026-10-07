class Dog:
    def speak(self): return "Bark"

class Cat:
    def speak(self): return "Meow"

class AnimalFactory:
    @staticmethod
    def create(kind):
        if kind == "dog":
            return Dog()
        elif kind == "cat":
            return Cat()
        raise ValueError("Unknown animal")

a = AnimalFactory.create("dog")
print(a.speak())    # Bark
