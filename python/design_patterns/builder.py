class Pizza:
    def __init__(self):
        self.size = None
        self.toppings = []

    def __str__(self):
        return f"{self.size} pizza with {self.toppings}"

class PizzaBuilder:
    def __init__(self):
        self.pizza = Pizza()

    def set_size(self, size):
        self.pizza.size = size
        return self                  # return self enables chaining

    def add_topping(self, topping):
        self.pizza.toppings.append(topping)
        return self

    def build(self):
        return self.pizza

pizza = (PizzaBuilder()
         .set_size("Large")
         .add_topping("Cheese")
         .add_topping("Olives")
         .build())


print(pizza)    # Large pizza with ['Cheese', 'Olives']
