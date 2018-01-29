import os
from flask_testing import LiveServerTestCase
import unittest
import urllib2
from flask import Flask
import requests

class FirstTest(LiveServerTestCase):

    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        # Default port is 5000
        app.config['LIVESERVER_PORT'] = 8943
        # Default timeout is 5 seconds
        app.config['LIVESERVER_TIMEOUT'] = 10
        return app

    def test_server_is_up_and_running(self):    
        urlFlask = 'http://ec2-52-14-116-91.us-east-2.compute.amazonaws.com/production'
        response = urllib2.urlopen(urlFlask)
        self.assertEqual(response.code, 200)
        self.postVals()

    def postVals(self):      
        data = {'onOff':'1', 'turnAngle':'43.0'}
        urlFlask = 'http://ec2-52-14-116-91.us-east-2.compute.amazonaws.com/production/post'
        r = requests.post(url = urlFlask, data = data)
        print 'RETURNED: '+r.text

if __name__ == '__main__':
    unittest.main()
