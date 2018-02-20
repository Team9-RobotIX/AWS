from flask_testing import LiveServerTestCase
import unittest
import requests
import flaskapp


class FirstTest(LiveServerTestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 0
        app.config['LIVESERVER_TIMEOUT'] = 10
        return app

    def setUp(self):
        print('setup')

    def test_server_is_up_and_running(self):
        url = self.get_server_url() + '/'
        r = requests.get(url = url)
        self.assertEquals(r.status_code, 200)
        print('Server is up and running')

    def test_post_vals_works_with_correct_vals(self):
        data = {'onOff': 1, 'turnAngle': 41.0}
        url = self.get_server_url() + '/post'
        r = requests.post(url = url, data = data)
        retData = eval(str(r.text))
        self.assertEqual(data['turnAngle'], retData['turnAngle'])
        self.assertEqual(data['onOff'], retData['onOff'])
        print('Successfully returned: ' + r.text)

    def test_post_vals_fails_with_invalid_turnangle(self):
        data = {'onOff': 1, 'turnAngle': 181.0}
        url = self.get_server_url() + '/post'
        r = requests.post(url = url, data = data)
        self.assertEqual('invalid request', r.text)
        print('Failed as expected: ' + r.text)

    def test_post_vals_fails_with_invalid_onoff(self):
        data = {'onOff': 2, 'turnAngle': 41.0}
        url = self.get_server_url() + '/post'
        r = requests.post(url = url, data = data)
        self.assertEqual('invalid request', r.text)
        print('Failed as expected: ' + r.text)

    def test_exception_handler(self):
        ret = flaskapp.exception_handler("error")
        self.assertEqual(ret, ("Oh no! 'error'", 400))

    def test_post_lock_works(self):
        data = {'lock': 1}
        urlPost = self.get_server_url() + '/lock'
        r = requests.post(url = urlPost, data = data)
        self.assertEqual(data['lock'], 1)
        print('Successfully returned: ' + r.text)

    def test_get_lock_flips_value(self):
        data = {'lock': 1}
        url = self.get_server_url() + '/lock'
        requests.post(url = url, data = data)
        valFirst = 1
        valExpectedNext = str(1 - int(valFirst))  # (1-0 = 1, 1-1=0)
        r2 = requests.get(url = url)
        self.assertEqual(str(r2.text), valExpectedNext)
        print('Successfully returned: ' + r2.text)

    def test_get_lock_default_value(self):
        url = self.get_server_url() + '/lock'
        r = requests.post(url = url)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.text, '1')

    def test_get_default_value(self):
        url = self.get_server_url() + '/'
        r = requests.get(url = url)
        print(r.text)
        self.assertEquals(r.status_code, 200)
        retData = eval(str(r.text))
        self.assertEquals(retData['onOff'], 0)
        self.assertEquals(retData['turnAngle'], 0.0)

    # Object tests
    def test_pacakge_init(self):
        # Package can be initialised without errors
        flaskapp.Package(1, 'package', 'desc', 3, 1, 5, 3600)

        # Package wuth minTemp higher than maxTemp raises error
        with self.assertRaises(ValueError):
            flaskapp.Package(2, 'package', 'desc', 3, 100, 0, 3600)

        # Package with negative time raises error
        with self.assertRaises(ValueError):
            flaskapp.Package(3, 'package', 'desc', 3, 1, 5, -1)

    def test_delivery_init(self):
        p1 = flaskapp.Package(1, 'package', 'desc', 3, 1, 5, 3600)
        pList = [p1]

        # Delivery can be initialised without errors
        flaskapp.Delivery(1, pList, 'A', 'B', 'PENDING')

        # Delivery with no packages raises an error
        with self.assertRaises(ValueError):
            flaskapp.Delivery(2, [], 'A', 'B', 'PENDING')

        p2 = flaskapp.Package(2, 'package', 'desc', 1, 1, 5, 3600)
        pList.append(p2)
        d3 = flaskapp.Delivery(3, pList, 'A', 'B', 'PENDING')

        # p1 has priority 3, p2 has priority 1 so delivery priority is 1.
        self.assertEqual(d3.priority, 1)

    def tearDown(self):
        print('teardown')


if __name__ == '__main__':
    unittest.main()
