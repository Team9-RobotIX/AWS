import flaskapp.config
import requests
import json


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
    env = flaskapp.config.Config

    username = get_username()
    password = get_password()

    try:
        r = requests.post('http://' + str(env.HOST) + ':5000/register', data = json.dumps({
            "username": username,
            "password": password
        }))

        if r.status_code == 200:
            print("User created successfully!")
            break
        else:
            print("Error creating user:")
            print(r.json['friendly'])
    except Exception as e:
        print("Failed to connect to server. Make sure the server is running before executing this script")
        print(e.message)
