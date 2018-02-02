from flask import Flask, request, jsonify
import sys, os, json
import heapq

app = Flask(__name__)
db = os.path.join(sys.path[0], "store.txt")


#Reads the stored values and outputs them.
@app.route('/', methods = ['GET', 'POST'])
def index():
    fh = open(db, "r")
    return fh.read()


#Demo of adding to and removing from the queue
@app.route('/getQueue', methods = ['GET', 'POST'])
def queuePage():
    h = []

    #Low priority delivery with 1 package
    pList1 = []
    p1 = Package(1, 'BloodSample', 'A sample of blood', -5, 3, 3600)
    pList1.append(p1)
    d1 = Delivery(1, pList1, 'A', 'B', 2, 'PENDING')

    #Medium priority delivery with 1 package
    pList2 = []
    p2 = Package(2, 'Shoe', 'A shoe', -5, 100, 100000)
    pList2.append(p2)
    d2 = Delivery(2, pList2, 'C', 'D', 3, 'PENDING')

    #High priority delivery with 2 packages
    pList3 = []
    p3 = Package(3, 'Heart', 'An actual human heart', -5, 5, 600)
    p4 = Package(4, 'Barack Obama', '44th President of the United States Barack Obama', -5, 40, 600)
    pList3.append(p3)
    pList3.append(p4)
    d3 = Delivery(3, pList3, 'B', 'D', 1, 'PENDING')

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
def post():

    #Get the expected params.
    onOff = request.values.get('onOff')
    turnAngle = request.values.get('turnAngle')

    #Check params are in expected ranges.
    if( (int(onOff) in [0,1]) and (-180 <= float(turnAngle) <= 180) ):

        #Open store.txt in write mode.
        fh = open(db, "w")

        #Store params as json and write to store.txt.
        jsonDict = json.dumps({"onOff":int(onOff), "turnAngle":float(turnAngle)})
        fh.write(jsonDict)
        fh.close()

        return str (jsonDict)
    else:
        return 'invalid request'

#Handle shutdown
@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


#Used if there is an error in the application.
@app.errorhandler(Exception)
def exception_handler(error):
    return "Oh no! "  + repr(error)


#Describes the item added to the delivery
class Package:
    def __init__(self, id, name, description, minTemp, maxTemp, timeLimit):
        self.id = id
        self.name = name
        self.description = description
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.timeLimit = timeLimit

#A delivery contains packages
class Delivery:
    def __init__(self, id, packageList, fromLoc, toLoc, priority, state):
        self.id = id
        self.packageList = packageList
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.priority = priority #Could be max of package priorities?
        self.state = state


def main():
    app.run()


if __name__ == '__main__':
  app.run()
