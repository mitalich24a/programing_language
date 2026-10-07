class Student:
    school = "ABC School"        # class variable (shared by all)

    def __init__(self, name):
        self.name = name         # instance variable (one per object)

print(Student.school)


class Demo:
    def __init__(self):
        self.name = "Ravi"        # public
        self._age = 20            # protected (convention only)
        self.__salary = 5000      # private (name mangled)
