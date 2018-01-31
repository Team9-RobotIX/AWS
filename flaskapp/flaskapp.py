from flask import Flask, request, jsonify
import sys, os, json

app = Flask(__name__)
db = os.path.join(sys.path[0], "store.txt")


#Reads the stored values and outputs them.
@app.route('/', methods = ['GET', 'POST'])
def index():
    fh = open(db, "r")
    return fh.read()


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

def main():
    app.run()


if __name__ == '__main__':
  app.run()
