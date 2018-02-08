from flask import Flask, request, jsonify, g
import sys, os, json
import heapq
import dataset
import shelve

app = Flask(__name__)
app.config.from_envvar('SERVER_SETTINGS')


def get_db():
    if not hasattr(g, 'db'):
        g.db = dataset.connect('sqlite:///development.db')
    return g.db


def get_cache():
    """
    The cache is meant to be a volatile data store backed by shelve.
    It can store arbitrary objects.
    """
    if not hasattr(g, 'cache'):
        g.cache = shelve.open('development_cache')
    return g.cache


@app.teardown_appcontext
def close_cache(error):
    if hasattr(g, 'cache'):
        g.cache.close()


#Reads the stored values and outputs them.
@app.route('/', methods = ['GET', 'POST'])
def index():
    onOff = get_cache()['onOff']
    turnAngle = get_cache()['turnAngle']
    return jsonify({'onOff': onOff, 'turnAngle': turnAngle})


#Demo of adding to and removing from the queue
@app.route('/getQueue', methods = ['GET', 'POST'])
                                                    #Ignore from tests
def queuePage():                                    # pragma: no cover
    h = []

    #Low priority delivery with 1 package
    pList1 = []
    p1 = Package(1, 'BloodSample', 'A sample of blood', 2, -5, 3, 3600)
    pList1.append(p1)
    d1 = Delivery(1, pList1, 'A', 'B', 'PENDING')

    #Medium priority delivery with 1 package
    pList2 = []
    p2 = Package(2, 'Shoe', 'A shoe', 3, -5, 100, 100000)
    pList2.append(p2)
    d2 = Delivery(2, pList2, 'C', 'D', 'PENDING')

    #High priority delivery with 2 packages
    pList3 = []
    p3 = Package(3, 'Heart', 'An actual human heart', 1, -5, 5, 600)
    p4 = Package(4, 'Barack Obama', '44th President of the United States Barack Obama', 1, -5, 40, 600)
    pList3.append(p3)
    pList3.append(p4)
    d3 = Delivery(3, pList3, 'B', 'D', 'PENDING')

    #Push all deliveries onto the heap queue
    heapq.heappush(h, (d1.priority, d1.packageList))
    heapq.heappush(h, (d2.priority, d2.packageList))
    heapq.heappush(h, (d3.priority, d3.packageList))

    #Get the list of packages in the Delivery
    d = heapq.heappop(h)[1]

    #Return the names of every package in the delivery
    return 'Queue: ' + str([x.name for x in d])



#Receives post request and stores input in store.txt.
@app.route('/post', methods = ['GET', 'POST'])
                                                    #Ignore from tests: already covered
def post():                                         # pragma: no cover

    #Get the expected params.
    onOff = int(request.values.get('onOff'))
    turnAngle = float(request.values.get('turnAngle'))

    #Check params are in expected ranges.
    if( (int(onOff) in [0,1]) and (-180 <= float(turnAngle) <= 180) ):
        get_cache()['onOff'] = onOff
        get_cache()['turnAngle'] = turnAngle
        return jsonify({'onOff': onOff, 'turnAngle': turnAngle})
    else:
        return 'invalid request'


@app.route('/lock', methods = ['GET', 'POST'])
def lock():
    #If 'POST' then write the new value
    if(request.values):
        lock = request.values.get('lock')

        #Check value in correct range
        if(lock in ['0','1']):
            get_cache()['lock'] = lock
        else:
            return 'invalid value'

    #Otherwise if 'GET' flip the value:
    else:
        get_cache()['lock'] = str(1 - int(get_cache()['lock']))

    #Return the value
    return get_cache()['lock']


#Used if there is an error in the application.
@app.errorhandler(Exception)
def exception_handler(error):
    return "Oh no! "  + repr(error)


#Describes the item added to the delivery
class Package:
    def __init__(self, id, name, description, priority, minTemp, maxTemp, timeLimit):
        self.id = id
        self.name = name
        self.description = description
        self.priority = priority
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.timeLimit = timeLimit
        if(minTemp > maxTemp):
            raise ValueError("Invalid temperatures")
        if(timeLimit < 0):
            raise ValueError("Invalid time limit")

#A delivery contains packages
class Delivery:
    def __init__(self, id, packageList, fromLoc, toLoc, state):
        self.id = id
        self.packageList = packageList
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.priority = min([x.priority for x in packageList]) #lowest number highest priority
        self.state = state
        if(len(packageList) < 1):
            raise ValueError("No packages")


def main():
    app.run()


if __name__ == '__main__':
    app.run()
