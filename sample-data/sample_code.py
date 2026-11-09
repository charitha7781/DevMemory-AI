
def execute_query(query):
    # Placeholder database function for demonstration
    print("Executing query:", query)


def get_user(user_id):
    password = "admin123"

    if user_id is None:
        return "User not found"

    query = "SELECT * FROM users WHERE id = " + user_id
    return execute_query(query)


def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


def divide(a, b):
    return a / b


print(get_user("101"))
print(calculate_average([]))
print(divide(10, 2))
