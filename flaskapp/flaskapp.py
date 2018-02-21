from flask import Flask, abort, request, jsonify, g
import heapq
import dataset
import shelve
import copy
from flask_bcrypt import Bcrypt
from classes import Package, Delivery, Instruction, Target
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


# Batch instructions route
@app.route('/instructions/batch', methods = ['GET'])
def instructions_batch_get():
    limit = request.values.get('limit')
    if limit is None:
        limit = len(get_cache()['instructions'])

    try:
        limit = int(limit)
    except Exception as e:
        return bad_request("Limit has to be positive integer")

    if 'instructions' not in get_cache():
        get_cache()['instructions'] = []
    elif len(get_cache()['instructions']) > 0 and limit <= 0:
        return bad_request("Limit has to be positive integer")

    instructions = get_cache()['instructions'][:limit]

    if 'correction' in get_cache():
        correction = {'angle': get_cache()['correction']}
        return jsonify({'instructions': instructions,
                        'correction': correction})
    else:
        return jsonify({'instructions': instructions})


# Instruction routes
@app.route('/instruction/<int:index>', methods = ['GET'])
def instruction_get(index):
    if 'instructions' not in get_cache():
        return file_not_found("This instruction does not exist")
    elif index >= len(get_cache()['instructions']) or index < 0:
        return file_not_found("This instruction does not exist")

    return jsonify(get_cache()['instructions'][index])


@app.route('/instruction/<int:index>', methods = ['DELETE'])
def instruction_delete(index):
    if 'instructions' not in get_cache():
        return file_not_found("This instruction does not exist")
    elif index >= len(get_cache()['instructions']) or index < 0:
        return file_not_found("This instruction does not exist")

    get_cache()['instructions'] = (get_cache()['instructions'][:index] +
                                   get_cache()['instructions'][index + 1:])

    return ''


# Correction routes
@app.route('/correction', methods = ['GET'])
def correction_get():
    if 'correction' not in get_cache():
        return file_not_found("No correction has been issued!")

    return jsonify({'angle': get_cache()['correction']})


@app.route('/correction', methods = ['POST'])
def correction_post():
    if 'correction' in get_cache():
        return bad_request("A correction has already been issued!")

    data = request.get_json(force=True)
    if 'angle' not in data:
        return bad_request("You have not supplied a correction angle!")
    elif not isinstance(data['angle'], float):
        return bad_request("Supplied angle is not a float")

    get_cache()['correction'] = data['angle']
    return jsonify({'angle': get_cache()['correction']})


@app.route('/correction', methods = ['DELETE'])
def correction_delete():
    if 'correction' not in get_cache():
        return file_not_found("No correction has been issued!")

    del get_cache()['correction']
    return ''


# Lock routes
@app.route('/lock', methods = ['GET'])
def lock_get():
    if 'locked' not in get_cache():
        get_cache()['locked'] = False

    return jsonify({'locked': get_cache()['locked']})


@app.route('/lock', methods = ['POST'])
def lock_post():
    data = request.get_json(force=True)

    if 'locked' not in data:
        return bad_request("Must supply a state for the lock.")
    elif not isinstance(data['locked'], bool):
        return bad_request("Invalid lock state supplied.")

    get_cache()['locked'] = data['locked']

    return jsonify({'locked': get_cache()['locked']})


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
