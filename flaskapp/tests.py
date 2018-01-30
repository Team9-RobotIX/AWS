import os
from flask_testing import LiveServerTestCase
import unittest
import urllib2
from flask import Flask
import json
import requests

class FirstTest(LiveServerTestCase):

    url = 'http://127.0.0.1:5000/'

    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        # Default port is 5000
        app.config['LIVESERVER_PORT'] = 8943
        # Default timeout is 5 seconds
        app.config['LIVESERVER_TIMEOUT'] = 10
        return app

    def test_server_is_up_and_running(self):
        response = urllib2.urlopen(self.url)
        self.assertEqual(response.code, 200)
        self.postVals()

    def postVals(self):
        data = {'onOff':1, 'turnAngle':41.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        retData = eval(str(r.text))
        self.assertEqual(data['turnAngle'], retData['turnAngle'])
        self.assertEqual(data['onOff'], retData['onOff'])
        print 'RETURNED: '+r.text

if __name__ == '__main__':
    unittest.main()
