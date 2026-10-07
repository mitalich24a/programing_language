class Account:
    def __init__(self):
        self.__balance = 0           # private

    @property
    def balance(self):               # getter
        return self.__balance

    @balance.setter
    def balance(self, value):        # setter with validation
        if value >= 0:
            self.__balance = value

a = Account()
a.balance = 500
print(a.balance)    # 500
