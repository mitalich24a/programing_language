class CreditCard:
    def pay(self, amt): print(f"Paid {amt} by Card")

class UPI:
    def pay(self, amt): print(f"Paid {amt} by UPI")

class Checkout:
    def __init__(self, strategy):
        self.strategy = strategy     # injected behavior

    def pay(self, amt):
        self.strategy.pay(amt)

Checkout(UPI()).pay(500)             # Paid 500 by UPI
Checkout(CreditCard()).pay(500)      # Paid 500 by Card
