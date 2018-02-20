from flask import Flask, abort, request, jsonify, g
import heapq
import dataset
import shelve
import copy
from flask_bcrypt import Bcrypt
from classes import Package, Delivery, Instruction
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
        g.cache = shelve.open(app.config['SHELVE_FILENAME'], protocol=2)
    return g.cache


@app.teardown_appcontext
def close_cache(error):
    if hasattr(g, 'cache'):
        g.cache.close()


# Reads the stored values and outputs them.
@app.route('/', methods = ['GET', 'POST'])
def index():
    if 'onOff' not in get_cache():
        get_cache()['onOff'] = 0

    if 'turnAngle' not in get_cache():
        get_cache()['turnAngle'] = 0.0

    onOff = get_cache()['onOff']
    turnAngle = get_cache()['turnAngle']
    return jsonify({'onOff': onOff, 'turnAngle': turnAngle})


@app.route('/login', methods = ['GET', 'POST'])
def login():
    username = request.values.get('username')
    password = request.values.get('password')

    usersTable = get_db()['users']
    user = usersTable.find_one(username=username)

    if(user):
        if(bcrypt.check_password_hash(user['password'], password)):
            return (str(username) + " " + str(password) +
                    " token: TOKEN_PLACEHOLDER")

    abort(401)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    username = request.values.get('username')
    password = request.values.get('password')
    hashedPassword = bcrypt.generate_password_hash(password)

    usersTable = get_db()['users']
    if(username and password and len(username) > 0 and len(password) > 0):
        usersTable.insert(dict(username=username, password=hashedPassword))
        return str(username) + " added"
    else:
        return "invalid username/password"


@app.route('/instructionsPost', methods = ['GET', 'POST'])
def instructions():
    instruction = request.values.get('instruction')
    value = request.values.get('value')
    get_cache()['instruction'] = instruction
    get_cache()['instructionValue'] = value
    return jsonify({'instruction': instruction, 'value': value})


@app.route('/getInstruction', methods = ['GET', 'POST'])
def getInstruction():
    instruction = get_cache()['instruction']
    value = get_cache()['instructionValue']
    return "instruction : " + str(instruction) + " value: " + str(value)


# Demo of adding to and removing from the queue
@app.route('/getQueue', methods = ['GET', 'POST'])
def queuePage():                                    # pragma: no cover
    h = []

    # Low priority delivery with 1 package
    pList1 = []
    p1 = Package(1, 'BloodSample', 'A sample of blood', 2, -5, 3, 3600)
    pList1.append(p1)
    d1 = Delivery(1, pList1, 'A', 'B', 'PENDING')

    # Medium priority delivery with 1 package
    pList2 = []
    p2 = Package(2, 'Shoe', 'A shoe', 3, -5, 100, 100000)
    pList2.append(p2)
    d2 = Delivery(2, pList2, 'C', 'D', 'PENDING')

    # High priority delivery with 2 packages
    pList3 = []
    p3 = Package(3, 'Heart', 'An actual human heart', 1, -5, 5, 600)
    p4 = Package(4, 'Barack Obama',
                 '44th President of the United States Barack Obama', 1,
                 -5, 40, 600)
    pList3.append(p3)
    pList3.append(p4)
    d3 = Delivery(3, pList3, 'B', 'D', 'PENDING')

    # Push all deliveries onto the heap queue
    heapq.heappush(h, (d1.priority, d1.packageList))
    heapq.heappush(h, (d2.priority, d2.packageList))
    heapq.heappush(h, (d3.priority, d3.packageList))

    # Get the list of packages in the Delivery
    d = heapq.heappop(h)[1]

    # Return the names of every package in the delivery
    return 'Queue: ' + str([x.name for x in d])


# Receives post request and stores input in store.txt.
@app.route('/post', methods = ['GET', 'POST'])
def post():                                         # pragma: no cover

    # Get the expected params.
    onOff = int(request.values.get('onOff'))
    turnAngle = float(request.values.get('turnAngle'))

    # Check params are in expected ranges.
    if( (int(onOff) in [0, 1]) and (-180 <= float(turnAngle) <= 180) ):
        get_cache()['onOff'] = onOff
        get_cache()['turnAngle'] = turnAngle
        return jsonify({'onOff': onOff, 'turnAngle': turnAngle})
    else:
        return 'invalid request'


@app.route('/lock', methods = ['GET', 'POST'])
def lock():
    if 'lock' not in get_cache():
        get_cache()['lock'] = 0

    # If 'POST' then write the new value
    if(request.values):
        lock = request.values.get('lock')

        # Check value in correct range
        if(lock in ['0', '1']):
            get_cache()['lock'] = lock
        else:
            return 'invalid value'

    # Otherwise if 'GET' flip the value:
    else:
        get_cache()['lock'] = str(1 - int(get_cache()['lock']))

    # Return the value
    return get_cache()['lock']


#                                         #
#              ROBOT ROUTES               #
#                                         #

# Instructions routes
@app.route('/instructions', methods = ['GET'])
def instructions_get():
    if 'instructions' not in get_cache():
        get_cache()['instructions'] = []

    return jsonify(get_cache()['instructions'])


@app.route('/instructions', methods = ['POST'])
def instructions_post():
    if 'instructions' not in get_cache():
        get_cache()['instructions'] = []

    data = request.get_json(force=True)

    new = copy.deepcopy(get_cache()['instructions'])
    if(isinstance(data, list)):  # Multiple instructions to be added
        for i in data:
            new.append(Instruction.from_dict(i))
    else:                        # Single instruction to be added
        new.append(Instruction.from_dict(data))

    get_cache()['instructions'] = new
    return jsonify(get_cache()['instructions'])


@app.route('/instructions', methods = ['DELETE'])
def instructions_delete():
    get_cache()['instructions'] = []
    return ''


# Used if there is an error in the application.
def bad_request(friendly):
    error_code = 400
    error = 'Bad request'

    data = {
        'code': error_code,
        'error': error,
        'friendly':  friendly
    }

    return data, 400


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
