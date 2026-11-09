
def execute_query(query):
    # Placeholder database function for demonstration
    print("Executing query:", query)


def get_user(user_id):
    password = "admin123"

    query = "SELECT * FROM users WHERE id = " + user_id

    if user_id != None:
        return execute_query(query)

    return "User not found"


def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


print(get_user("101"))
print(calculate_average([]))
