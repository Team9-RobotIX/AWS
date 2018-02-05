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

    def setUp(self):
        print 'setup'

    ###This must be first
    def test_shutdown_text_outputted(self):
        r = requests.post(url = self.url + 'shutdown', data = {})
        self.assertEqual(r.text, 'Server shutting down...')

    def test_shutdown_error_outputted(self):
        with self.assertRaises(RuntimeError):
            r = flaskapp.shutdown()
            print 'Errored as expected: '+r.text

    def test_server_is_up_and_running(self):
        print self.get_server_url()
        response = urllib2.urlopen(self.url)
        self.assertEqual(response.code, 200)
        print 'Server is up and running'

    def test_post_vals_works_with_correct_vals(self):
        data = {'onOff':1, 'turnAngle':41.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        retData = eval(str(r.text))
        self.assertEqual(data['turnAngle'], retData['turnAngle'])
        self.assertEqual(data['onOff'], retData['onOff'])
        print 'Successfully returned: '+r.text

    def test_post_vals_fails_with_invalid_turnangle(self):
        data = {'onOff':1, 'turnAngle':181.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        self.assertEqual('invalid request', r.text)
        print 'Failed as expected: '+r.text

    def test_post_vals_fails_with_invalid_onoff(self):
        data = {'onOff':2, 'turnAngle':41.0}
        urlPost = self.url + 'post'
        r = requests.post(url = urlPost, data = data)
        self.assertEqual('invalid request', r.text)
        print 'Failed as expected: '+r.text

    def test_exception_handler(self):
        ret = flaskapp.exception_handler("error")
        self.assertEqual(ret, "Oh no! 'error'")


    #Object tests
    def test_pacakge_init(self):

        #Package can be initialised without errors
        p1 = flaskapp.Package(1, 'package', 'desc', 3, 1, 5, 3600)

        #Package wuth minTemp higher than maxTemp raises error
        with self.assertRaises(ValueError):
            p2 = flaskapp.Package(2, 'package', 'desc', 3, 100, 0, 3600)

        #Package with negative time raises error
        with self.assertRaises(ValueError):
            p3 = flaskapp.Package(3, 'package', 'desc', 3, 1, 5, -1)

    def test_delivery_init(self):
        p1 = flaskapp.Package(1, 'package', 'desc', 3, 1, 5, 3600)
        pList = [p1]

        #Delivery can be initialised without errors
        d1 = flaskapp.Delivery(1, pList, 'A', 'B', 'PENDING')

        #Delivery with no packages raises an error
        with self.assertRaises(ValueError):
            d2 = flaskapp.Delivery(2, [], 'A', 'B', 'PENDING')

        p2 = flaskapp.Package(2, 'package', 'desc', 1, 1, 5, 3600)
        pList.append(p2)
        d3 = flaskapp.Delivery(3, pList, 'A', 'B', 'PENDING')

        #p1 has priority 3, p2 has priority 1 so delivery priority is 1.
        self.assertEqual(d3.priority, 1)


    def tearDown(self):
        print 'teardown'

if __name__ == '__main__':

    server = Process(target=flaskapp.main)
    server.start()
    unittest.main()
