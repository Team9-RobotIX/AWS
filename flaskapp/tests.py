import os
from flask_testing import LiveServerTestCase
import unittest
import urllib2
from flask import Flask
import json
import requests
import flaskapp

from multiprocessing import Process

import time

class FirstTest(LiveServerTestCase):

    #Local url
    url = 'http://127.0.0.1:5000/'

    #Initialise testing app
    def create_app(self):
        app = Flask(__name__)
        #app.config['TESTING'] = True
        # Default port is 5000
        app.config['LIVESERVER_PORT'] = 8943
        # Default timeout is 5 seconds
        app.config['LIVESERVER_TIMEOUT'] = 10
        return app

    def test_runAll(self):
        self.server_is_up_and_running_test()
        self.post_vals_works_with_correct_vals_test()
        self.post_vals_fails_with_invalid_turnangle_test()
        self.post_vals_fails_with_invalid_onoff_test()
        print 'all tests have run, shutting down'
        r = requests.post(url = self.url + 'shutdown', data = {})

    #Test that the server is responding
    def server_is_up_and_running_test(self):
        print self.get_server_url()
        response = urllib2.urlopen(self.url)
        self.assertEqual(response.code, 200)
        print 'Server is up and running'

    def post_vals_works_with_correct_vals_test(self):
        data = {'onOff':1, 'turnAngle':41.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        retData = eval(str(r.text))
        self.assertEqual(data['turnAngle'], retData['turnAngle'])
        self.assertEqual(data['onOff'], retData['onOff'])
        print 'Successfully returned: '+r.text

    def post_vals_fails_with_invalid_turnangle_test(self):
        data = {'onOff':1, 'turnAngle':181.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        self.assertEqual('invalid request', r.text)
        print 'Failed as expected: '+r.text

    def post_vals_fails_with_invalid_onoff_test(self):
        data = {'onOff':2, 'turnAngle':41.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        self.assertEqual('invalid request', r.text)
        print 'Failed as expected: '+r.text

if __name__ == '__main__':

    server = Process(target=flaskapp.main)
    server.start()
    unittest.main()
