from flask import Flask, request, jsonify
import sys, os, json

app = Flask(__name__)


#Reads the stored values and outputs them.
@app.route('/', methods = ['GET', 'POST'])
def index():
    fh = open("/home/ubuntu/flaskapp/store.txt", "r")
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
        fh = open("/home/ubuntu/flaskapp/store.txt", "w")
        
        #Store params as json and write to store.txt.
        jsonDict = json.dumps({"onOff:":int(onOff), "turnAngle":float(turnAngle)})
        fh.write(jsonDict)                    
        fh.close()

        return 'Successfully set onOff:'+str(onOff) +' turnAngle: '+str(turnAngle) 
    else:
        return 'invalid request'


#Used if there is an error in the application.
@app.errorhandler(Exception)
def exception_handler(error):
    return "Oh no!"  + repr(error)


if __name__ == '__main__':
  app.run()
