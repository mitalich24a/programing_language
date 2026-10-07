class Demo:
    count = 0

    def instance_method(self):       # uses self
        print("instance")

    @classmethod
    def class_method(cls):           # uses cls
        print("class", cls.count)

    @staticmethod
    def static_method():             # uses neither
        print("static")

# Calling

d = Demo()                  # create an object first

d.instance_method()         # needs an object
# Demo.instance_method()    # TypeError: missing 'self'

Demo.class_method()         # via class (most common)
d.class_method()            # via object also works

Demo.static_method()        # via class
d.static_method()           # via object also works
