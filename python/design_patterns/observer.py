class Subject:
    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def notify(self, msg):
        for o in self.observers:
            o.update(msg)

class EmailUser:
    def update(self, msg): print(f"Email: {msg}")

class SMSUser:
    def update(self, msg): print(f"SMS: {msg}")

channel = Subject()
channel.subscribe(EmailUser())
channel.subscribe(SMSUser())

channel.notify("New video uploaded!")
# Email: New video uploaded!
# SMS: New video uploaded!
