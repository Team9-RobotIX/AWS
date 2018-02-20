from flask_testing import TestCase, LiveServerTestCase
import json
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

    def test_server_is_up_and_running(self):
        route = '/'
        url = self.get_server_url() + route
        r = requests.get(url = url)
        self.assertEquals(r.status_code, 200)
        print('Server is up and running')

    def test_post_vals_works_with_correct_vals(self):
        data = {'onOff': 1, 'turnAngle': 41.0}
        route = '/post'
        url = self.get_server_url() + route
        r = requests.post(url = url, data = data)
        retData = eval(str(r.text))
        self.assertEqual(data['turnAngle'], retData['turnAngle'])
        self.assertEqual(data['onOff'], retData['onOff'])
        print('Successfully returned: ' + r.text)

    def test_post_vals_fails_with_invalid_turnangle(self):
        data = {'onOff': 1, 'turnAngle': 181.0}
        route = '/post'
        url = self.get_server_url() + route
        r = requests.post(url = url, data = data)
        self.assertEqual('invalid request', r.text)
        print('Failed as expected: ' + r.text)

    def test_post_vals_fails_with_invalid_onoff(self):
        data = {'onOff': 2, 'turnAngle': 41.0}
        route = '/post'
        url = self.get_server_url() + route
        r = requests.post(url = url, data = data)
        self.assertEqual('invalid request', r.text)
        print('Failed as expected: ' + r.text)

    def test_exception_handler(self):
        ret = flaskapp.exception_handler("error")
        self.assertEqual(ret, ("Oh no! 'error'", 400))

    def test_get_default_value(self):
        route = '/'
        url = self.get_server_url() + route
        r = requests.get(url = url)
        print(r.text)
        self.assertEquals(r.status_code, 200)
        retData = eval(str(r.text))
        self.assertEquals(retData['onOff'], 0)
        self.assertEquals(retData['turnAngle'], 0.0)


class RobotGroupTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    # Instruction routes
    def test_delete_instructions(self):
        route = '/instructions'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 200)

    def test_get_instructions_queue_empty(self):
        route = '/instructions'
        self.client.delete(route)

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_get_instructions(self):
        route = '/instructions'
        self.client.delete(route)

        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90}]
        self.client.post(route, data = json.dumps(data))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_instructions_single(self):
        route = '/instructions'
        self.client.delete(route)

        data = {'type': 'MOVE', 'value': 100}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [data])

    def test_post_instructions_multiple(self):
        route = '/instructions'
        self.client.delete(route)

        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90}]
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_instructions_fails_with_missing_type(self):
        route = '/instructions'
        self.client.delete(route)

        data = [{'value': 100}]
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_instructions_fails_with_missing_value(self):
        route = '/instructions'
        self.client.delete(route)

        data = [{'type': 'MOVE'}]
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_instructions_fails_with_invalid_type(self):
        route = '/instructions'
        self.client.delete(route)

        data = [{'type': 'HALT', 'value': 100}]
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_instructions_fails_with_bad_angle(self):
        route = '/instructions'
        self.client.delete(route)

        data = [{'type': 'TURN', 'value': 190.0}]
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Lock routes
    def test_post_lock_set_true(self):
        data = {'locked': True}
        route = '/lock'
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_lock_set_false(self):
        data = {'locked': True}
        route = '/lock'
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_get_lock_false(self):
        route = '/lock'
        data = {'locked': False}
        self.client.post(route, data = json.dumps(data))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_get_lock_true(self):
        route = '/lock'
        data = {'locked': True}
        self.client.post(route, data = json.dumps(data))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)


class DataStructureTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

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


if __name__ == '__main__':
    unittest.main()
