import config


env = config.Config


def get_username():
    val = raw_input("Username: ")      # NOQA
    if len(val) <= 0:
        print("Username must have length of at least 1.")
        return get_username()
    return val


def get_password():
    val = raw_input("Password: ")      # NOQA
    if len(val) <= 0:
        print("Password must have length of at least 1.")
        return get_password()
    return val


repeat = True
print("Welcome to RobotIX's user creation wizard!\n")

while repeat:
    repeat = False

    username = get_username()
    password = get_password()

