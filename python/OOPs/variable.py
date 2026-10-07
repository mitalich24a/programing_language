class Student:
    school = "ABC School"        # class variable (shared by all)

    def __init__(self, name):
        self.name = name         # instance variable (one per object)

print(Student.school)
