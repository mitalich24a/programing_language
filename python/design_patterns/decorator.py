def log(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print("Done")
        return result
    return wrapper

@log
def add(a, b):
    return a + b

print(add(2, 3))
# Calling add
# Done
# 5
