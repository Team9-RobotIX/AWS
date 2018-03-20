from flask import Flask, request, jsonify, g
import dataset
import shelve
import copy
import random
import string
from flask_bcrypt import Bcrypt
from classes import Delivery, Robot, Target, DeliveryState
from encoder import CustomJSONEncoder

app = Flask(__name__)
app.config.from_object('config.Config')
app.json_encoder = CustomJSONEncoder
bcrypt = Bcrypt(app)


def get_db():
    if not hasattr(g, 'db'):
        g.db = dataset.connect(app.config['DATASET_DATABASE_URI'])
    return g.db


def get_cache():
    """
    The cache is meant to be a volatile data store backed by shelve.
    It can store arbitrary objects.
    """
    if not hasattr(g, 'cache'):
        g.cache = shelve.open(app.config['SHELVE_FILENAME'], protocol=2,
                              writeback=True)
    return g.cache


def generate_bearer_token():
    return ''.join([random.choice(string.ascii_letters + string.digits)
                    for n in range(32)])


def generate_challenge_token():
    return ''.join([random.choice(string.ascii_letters + string.digits)
                    for n in range(10)])


class InvalidBearerException(Exception):
    pass


def get_username(headers):
    if 'Authorization' not in headers:
        raise InvalidBearerException("No Authorization header found.")
    if not headers['Authorization'].startswith("Bearer "):
        raise InvalidBearerException("Authorization method must be bearer.")
    if len(headers['Authorization'][7:]) != 32:
        raise InvalidBearerException("Bearer token invalid.")

    bearer = headers['Authorization'][7:]
    usersTable = get_db()['users']
    user = usersTable.find_one(bearer=bearer)

    if user is None:
        raise InvalidBearerException("This bearer token is invalid.")

    return user['username']


@app.teardown_appcontext
def close_cache(error):
    if hasattr(g, 'cache'):
        g.cache.close()


# Reads the stored values and outputs them.
@app.route('/login', methods = ['POST'])
def login():
    data = request.get_json(force=True)
    if 'username' not in data:
        return bad_request("Missing username")
    if 'password' not in data:
        return bad_request("Missing password")

    username = data['username']
    password = data['password']

    usersTable = get_db()['users']
    user = usersTable.find_one(username=username)
    if(user):
        if(bcrypt.check_password_hash(user['password'], password)):
            token = generate_bearer_token()
            usersTable.update({"username": username, "bearer": token},
                              ['username'])
            return jsonify({'bearer': token})

    return unauthorized("No such username/password combination")


@app.route('/register', methods = ['POST'])
def register():
    data = request.get_json(force=True)
    if 'username' not in data:
        return bad_request("Missing username")
    if 'password' not in data:
        return bad_request("Missing password")

    username = data['username']
    password = data['password']
    hashedPassword = bcrypt.generate_password_hash(password)

    usersTable = get_db()['users']
    user = usersTable.find_one(username=username)
    if user is not None:
        return bad_request("This username is already taken.")

    if(username and password and len(username) > 0 and len(password) > 0):
        usersTable.insert(dict(username=username, password=hashedPassword,
                               bearer=''))
        return ''
    else:
        return bad_request("Invalid username/password")


#                                            #
#              DELIVERY ROUTES               #
#                                            #
@app.route('/deliveries', methods = ['GET'])
def deliveries_get():
    if 'deliveryQueue' not in get_cache():
        get_cache()['deliveryQueue'] = []

    return jsonify([x[2] for x in get_cache()['deliveryQueue']])


@app.route('/deliveries', methods = ['POST'])
def deliveries_post():
    if 'deliveryQueue' not in get_cache():
        get_cache()['deliveryQueue'] = []

    if 'deliveryQueueCounter' not in get_cache():
        get_cache()['deliveryQueueCounter'] = 0

    data = request.get_json(force=True)
    counter = get_cache()['deliveryQueueCounter']

    # Error checking
    if 'name' not in data:
        return bad_request("Must provde a name")
    if not isinstance(data['name'], basestring):        # NOQA
        return bad_request("Name must be string")
    if ('description' in data and not isinstance(data['description'], basestring)):        # NOQA
        return bad_request("Description must be string")
    if 'priority' not in data:
        return bad_request("Must provide a priority")
    if not isinstance(data['priority'], int):
        return bad_request("Priority must be integer")
    if 'sender' not in data or 'receiver' not in data:
        return bad_request("Must provide both a sender and a receiver")
    if (not isinstance(data['sender'], basestring) or       # NOQA
            not isinstance(data['receiver'], basestring)):  # NOQA
        return bad_request("Must provide both a sender and a receiver")

    targetsTable = get_db()['targets']
    fromTarget = targetsTable.find_one(id=data['from'])
    toTarget = targetsTable.find_one(id=data['to'])

    try:
        username = get_username(request.headers)
    except InvalidBearerException as e:
        return unauthorized(e.message)

    if fromTarget is None:
        return bad_request("From target doesn't exist")

    if toTarget is None:
        return bad_request("To target doesn't exist")

    usersTable = get_db()['users']
    senderUser = usersTable.find_one(username=data['sender'])
    receiverUser = usersTable.find_one(username=data['receiver'])

    if data['sender'] != username:
        return bad_request("Sender has to be logged in user.")

    if senderUser is None:
        return bad_request("Sender user doesn't exist")

    if receiverUser is None:
        return bad_request("Receiver user doesn't exist")

    if 'description' in data:
        d = Delivery(counter, fromTarget, toTarget, data['sender'],
                     data['receiver'], data['priority'], data['name'],
                     data['description'])
    else:
        d = Delivery(counter, fromTarget, toTarget, data['sender'],
                     data['receiver'], data['priority'], data['name'])

    h = copy.deepcopy(get_cache()['deliveryQueue'])
    h.append((d.priority, counter, d))
    h = sorted(h, key = lambda x: (x[0], x[1]))

    get_cache()['deliveryQueueCounter'] += 1
    get_cache()['deliveryQueue'] = h

    return delivery_get(counter)


@app.route('/deliveries', methods = ['DELETE'])
def deliveries_delete():
    if 'deliveryQueue' in get_cache():
        get_cache()['deliveryQueue'] = []
        get_cache()['deliveryQueueCounter'] = 0

    if 'challenge_token' in get_cache():
        del get_cache()['challenge_token']

    get_cache()['deliveryQueueCounter'] = 0

    return ''


# Delivery route
@app.route('/delivery/<int:id>', methods = ['GET'])
def delivery_get(id):
    if 'deliveryQueue' not in get_cache():
        get_cache()['deliveryQueue'] = []

    item = [x[2] for x in get_cache()['deliveryQueue'] if x[1] == id]
    if len(item) <= 0:
        return file_not_found("There's no delivery with that ID!")

    return jsonify(item[0])


@app.route('/delivery/<int:id>', methods = ['PATCH'])
def delivery_patch(id):
    data = request.get_json(force=True)
    return patch_delivery_with_json(id, data)


def patch_delivery_with_json(id, data):
    if 'deliveryQueue' not in get_cache():
        get_cache()['deliveryQueue'] = []

    if 'deliveryQueue' not in get_cache():
        get_cache()['deliveryQueue'] = []

    index = -1
    for idx, d in enumerate(get_cache()['deliveryQueue']):
        if d[1] == id:
            index = idx
            break

    if index < 0:
        return file_not_found("There's no delivery with that ID!")

    if 'state' not in data:
        return bad_request("Missing state")
    if data['state'] not in [e.name for e in DeliveryState]:
        return bad_request("Invalid state")

    new = copy.deepcopy(get_cache()['deliveryQueue'])
    new[index][2].state = DeliveryState[data['state']]

    lock_state_mapping = {
        DeliveryState.MOVING_TO_SOURCE: True,
        DeliveryState.AWAITING_AUTHENTICATION_SENDER: True,
        DeliveryState.AWAITING_PACKAGE_LOAD: False,
        DeliveryState.PACKAGE_LOAD_COMPLETE: True,
        DeliveryState.MOVING_TO_DESTINATION: True,
        DeliveryState.AWAITING_AUTHENTICATION_RECEIVER: True,
        DeliveryState.AWAITING_PACKAGE_RETRIEVAL: False,
        DeliveryState.PACKAGE_RETRIEVAL_COMPLETE: True,
        DeliveryState.COMPLETE: True
    }

    # Temporary fix for #54
    if new[index][2].state in lock_state_mapping:
        new_state = new[index][2].state
        get_cache()['locked'] = lock_state_mapping[new_state]
    else:
        get_cache()['locked'] = False

    if new[index][2].state == DeliveryState.AWAITING_AUTHENTICATION_SENDER:
        get_cache()['challenge_token'] = generate_challenge_token()
    if new[index][2].state == DeliveryState.AWAITING_AUTHENTICATION_RECEIVER:
        get_cache()['challenge_token'] = generate_challenge_token()

    get_cache()['deliveryQueue'] = new
    return delivery_get(id)


@app.route('/delivery/<int:id>', methods = ['DELETE'])
def delivery_delete(id):
    if 'deliveryQueue' not in get_cache():
        get_cache()['deliveryQueue'] = []

    item = [x[2] for x in get_cache()['deliveryQueue'] if x[1] == id]
    if len(item) <= 0:
        return file_not_found("There's no delivery with that ID!")

    items = [x for x in get_cache()['deliveryQueue'] if x[1] != id]
    get_cache()['deliveryQueue'] = items
    return ''


#                                          #
#              TARGET ROUTES               #
#                                          #
@app.route('/targets', methods = ['GET'])
def targets_get():
    targetsTable = get_db()['targets']
    targets = targetsTable.all()

    result = []
    for t in targets:
        result.append(Target.from_dict(t))

    return jsonify(result)


@app.route('/targets', methods = ['POST'])
def targets_post():
    targetsTable = get_db()['targets']
    data = request.get_json(force=True)

    if 'name' not in data:
        return bad_request("Must provide name for target.")
    elif not isinstance(data['name'], basestring):  # NOQA
        return bad_request("Name must be string")
    elif 'description' in data and not isinstance(data['description'], basestring):  # NOQA
        return bad_request("Description must be string")
    elif 'color' in data and not isinstance(data['color'], str):
        return bad_request("Color must be string")

    obj = {
        'name': data['name']
    }

    if 'description' in data:
        obj['description'] = data['description']

    if 'color' in data:
        obj['color'] = data['color']

    targetsTable.insert(obj)

    return targets_get()


@app.route('/targets', methods = ['DELETE'])
def targets_delete():
    targetsTable = get_db()['targets']
    targetsTable.drop()
    return ''


@app.route('/target/<int:id>', methods = ['GET'])
def target_get(id):
    targetsTable = get_db()['targets']

    if id < 0:
        return file_not_found("Target must be positive integer")

    target = targetsTable.find_one(id=id)
    if target is None:
        return file_not_found("This target does not exist")

    return jsonify(Target.from_dict(target))


@app.route('/target/<int:id>', methods = ['PATCH'])
def target_patch(id):
    targetsTable = get_db()['targets']

    if id < 0:
        return file_not_found("Target must be positive integer")

    target = targetsTable.find_one(id=id)
    if target is None:
        return file_not_found("This target does not exist")

    data = request.get_json(force=True)
    if 'color' in data:
        if not isinstance(data['color'], basestring):  # NOQA
            return bad_request("Color must be of type string")

        targetsTable.update({'id': id, 'color': data['color']}, ['id'])

    return target_get(id)


@app.route('/target/<int:id>', methods = ['DELETE'])
def target_delete(id):
    targetsTable = get_db()['targets']

    if id < 0:
        return file_not_found("Target must be positive integer")

    target = targetsTable.find_one(id=id)
    if target is None:
        return file_not_found("This target does not exist")

    targetsTable.delete(id=id)

    return ''


#                                         #
#              ROBOT ROUTES               #
#                                         #
def get_robot(id):
    if 'robots' not in get_cache():
        get_cache()['robots'] = dict()

    if id not in get_cache()['robots']:
        get_cache()['robots'][id] = Robot(id)

    return get_cache()['robots'][id]


# Batch instructions route
@app.route('/robot/<int:id>/batch', methods = ['GET'])
def robot_batch_get(id):
    response = {}

    r = get_robot(id)
    response['correction'] = r.correction
    response['angle'] = r.angle
    response['motor'] = r.motor
    response['distance'] = r.distance

    if 'challenge_token' in get_cache():
        response['token'] = get_cache()['challenge_token']

    return jsonify(response)


# Correction routes
@app.route('/robot/<int:id>/correction', methods = ['GET'])
def robot_correction_get(id):
    r = get_robot(id)
    return jsonify({'correction': r.correction})


@app.route('/robot/<int:id>/correction', methods = ['POST'])
def robot_correction_post(id):
    data = request.get_json(force=True)
    if 'correction' not in data:
        return bad_request("You have not supplied a correction angle!")
    elif not isinstance(data['correction'], float):
        return bad_request("Supplied angle is not a float")

    r = get_robot(id)
    r.correction = data['correction']
    return robot_correction_get(id)


# Angle routes
@app.route('/robot/<int:id>/angle', methods = ['GET'])
def robot_angle_get(id):
    r = get_robot(id)
    return jsonify({'angle': r.angle})


@app.route('/robot/<int:id>/angle', methods = ['POST'])
def robot_angle_post(id):
    data = request.get_json(force=True)
    if 'angle' not in data:
        return bad_request("You have not supplied an angle!")
    elif not isinstance(data['angle'], float):
        return bad_request("Supplied angle is not a float")

    r = get_robot(id)
    r.angle = data['angle']
    return robot_angle_get(id)


# Distance routes
@app.route('/robot/<int:id>/distance', methods = ['GET'])
def robot_distance_get(id):
    r = get_robot(id)
    return jsonify({'distance': r.distance})


@app.route('/robot/<int:id>/distance', methods = ['POST'])
def robot_distance_post(id):
    data = request.get_json(force=True)
    if 'distance' not in data:
        return bad_request("You have not supplied a distance!")
    elif not isinstance(data['distance'], float):
        return bad_request("Supplied distance is not a float")

    r = get_robot(id)
    r.distance = data['distance']
    return robot_distance_get(id)


# Motor routes
@app.route('/robot/<int:id>/motor', methods = ['GET'])
def robot_motor_get(id):
    r = get_robot(id)
    return jsonify({'motor': r.motor})


@app.route('/robot/<int:id>/motor', methods = ['POST'])
def robot_motor_post(id):
    data = request.get_json(force=True)
    if 'motor' not in data:
        return bad_request("You have not supplied a motor state!")
    elif not isinstance(data['motor'], bool):
        return bad_request("Supplied motor state is not a bool")

    r = get_robot(id)
    r.motor = data['motor']
    return robot_motor_get(id)


# Lock routes
@app.route('/robot/<int:id>/lock', methods = ['GET'])
def robot_lock_get(id):
    r = get_robot(id)
    return jsonify({'lock': r.lock})


@app.route('/robot/<int:id>/lock', methods = ['POST'])
def robot_lock_post(id):
    data = request.get_json(force=True)
    if 'lock' not in data:
        return bad_request("You have not supplied a lock state!")
    elif not isinstance(data['lock'], bool):
        return bad_request("Supplied lock state is not a bool")

    r = get_robot(id)
    r.lock = data['lock']
    return robot_lock_get(id)


# Verify routes
@app.route('/verify', methods = ['POST'])
def verify_post():
    data = request.get_json(force=True)

    if 'token' not in data:
        return bad_request("Must supply a challenge token")
    elif not isinstance(data['token'], basestring):         # NOQA
        return bad_request("Challenge token must be string")

    try:
        username = get_username(request.headers)
    except InvalidBearerException as e:
        return unauthorized(e.message)

    if data['token'] != get_cache()['challenge_token']:
        return unauthorized("Challenge token doesn't match QR")

    delivery = None
    delivery_id = -1
    for d in get_cache()['deliveryQueue']:
        if (d[2].state == DeliveryState.AWAITING_AUTHENTICATION_SENDER or
                d[2].state == DeliveryState.AWAITING_AUTHENTICATION_RECEIVER):
            delivery = d[2]
            delivery_id = d[1]
            break

    if delivery_id < 0:
        return bad_request("No deliveries awaiting authentication")

    if delivery.state == DeliveryState.AWAITING_AUTHENTICATION_SENDER:
        if delivery.sender == username:
            del get_cache()['challenge_token']
            patch_delivery_with_json(delivery_id, {"state":
                                                   "AWAITING_PACKAGE_LOAD"})
            return ''

    if delivery.state == DeliveryState.AWAITING_AUTHENTICATION_RECEIVER:
        if delivery.receiver == username:
            del get_cache()['challenge_token']
            patch_delivery_with_json(delivery_id,
                                     {"state": "AWAITING_PACKAGE_RETRIEVAL"})
            return ''

    return unauthorized("You are not allowed to open the box!")


# Used if there is an error in the application.
def bad_request(friendly):
    error_code = 400
    error = 'Bad request'

    data = {
        'code': error_code,
        'error': error,
        'friendly':  friendly
    }

    return jsonify(data), error_code


def unauthorized(friendly):
    error_code = 401
    error = 'Unauthorized access'

    data = {
        'code': error_code,
        'error': error,
        'friendly':  friendly
    }

    return jsonify(data), error_code


def file_not_found(friendly):
    error_code = 404
    error = 'File not found'

    data = {
        'code': error_code,
        'error': error,
        'friendly':  friendly
    }

    return jsonify(data), error_code


@app.errorhandler(Exception)
def exception_handler(error):
    return "Oh no! "  + repr(error), 400


@app.errorhandler(401)
def custom_401(error):
    return 'Access denied', 401


def main():
    app.run()


if __name__ == '__main__':
    app.run()
