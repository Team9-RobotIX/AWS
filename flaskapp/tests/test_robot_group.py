from flask_testing import TestCase
import json
import unittest
import flaskapp


class RobotGroupTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    def setUp(self):
        self.routeBase = '/robot/0'
        self.clear_all_robot_fields()

    # Helper methods
    def check_response_match(self, expected, res):
        for k, v in expected.iteritems():
            self.assertTrue(k in res)
            self.assertEquals(v, res[k])

    def post_correction(self, value):
        data = {'correction': value}
        return self.client.post(self.routeBase + '/correction',
                                data = json.dumps(data))

    def post_angle(self, value):
        data = {'angle': value}
        return self.client.post(self.routeBase + '/angle',
                                data = json.dumps(data))

    def post_motor(self, value):
        data = {'motor': value}
        return self.client.post(self.routeBase + '/motor',
                                data = json.dumps(data))

    def post_distance(self, value):
        data = {'distance': value}
        return self.client.post(self.routeBase + '/distance',
                                data = json.dumps(data))

    def get_batch(self):
        return self.client.get(self.routeBase + '/batch')

    def clear_all_robot_fields(self):
        self.post_correction(0.0)
        self.post_angle(0.0)
        self.post_motor(False)
        self.post_distance(0.0)

    def check_batch_get_response_match(self, data):
        r = self.get_batch()
        self.assertEquals(r.status_code, 200)
        self.check_response_match(data, r.json)
        return data

    # Batch instructions route
    def test_get_batch_empty(self):
        data = {
            'angle': 0.0,
            'correction': 0.0,
            'motor': False,
            'distance': 0.0
        }

        self.check_batch_get_response_match(data)

    def test_get_batch_changes_individually(self):
        data = {
            'angle': 0.0,
            'correction': 0.0,
            'motor': False,
            'distance': 0.0
        }

        # Check 'angle' changes correctly
        data['angle'] = 23.0
        r = self.post_angle(data['angle'])
        self.assertEquals(r.status_code, 200)
        self.check_batch_get_response_match(data)

        # Check 'correction' changes correctly
        data['correction'] = 74.0
        r = self.post_correction(data['correction'])
        self.assertEquals(r.status_code, 200)
        self.check_batch_get_response_match(data)

        # Check 'motor' changes correctly
        data['motor'] = True
        r = self.post_motor(data['motor'])
        self.assertEquals(r.status_code, 200)
        self.check_batch_get_response_match(data)

        # Check 'distance' changes correctly
        data['distance'] = 99.0
        r = self.post_distance(data['distance'])
        self.assertEquals(r.status_code, 200)
        self.check_batch_get_response_match(data)

    def test_post_batch_no_changes_invalid_updates(self):
        data = {
            'angle': 0.0,
            'correction': 0.0,
            'motor': False,
            'distance': 0.0
        }

        # Check 'angle' changes correctly
        r = self.post_angle('asd')
        self.assertEquals(r.status_code, 400)
        self.check_batch_get_response_match(data)

        # Check 'correction' changes correctly
        r = self.post_correction('asdasd')
        self.assertEquals(r.status_code, 400)
        self.check_batch_get_response_match(data)

        # Check 'motor' changes correctly
        r = self.post_motor('asdasd')
        self.assertEquals(r.status_code, 400)
        self.check_batch_get_response_match(data)

        # Check 'distance' changes correctly
        r = self.post_correction('asdasd')
        self.assertEquals(r.status_code, 400)
        self.check_batch_get_response_match(data)

    def test_post_batch(self):
        data = {
            'angle': 0.0,
            'correction': 0.0,
            'motor': False,
            'distance': 0.0
        }
        self.check_batch_get_response_match(data)

        # Check 'angle' changes correctly
        data['angle'] = 23.0
        data['correction'] = 66.0
        data['motor'] = True
        data['distance'] = 88.0
        r = self.client.post(self.routeBase + '/batch',
                             data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.check_batch_get_response_match(data)

    def test_post_batch_error_null_input(self):
        r = self.client.post(self.routeBase + '/batch', data = '')
        self.assertEquals(r.status_code, 400)

    def test_post_batch_error_invalid_angle(self):
        data = {'angle': 'asd'}
        r = self.client.post(self.routeBase + '/batch',
                             data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_batch_error_invalid_correction(self):
        data = {'correction': 'asd'}
        r = self.client.post(self.routeBase + '/batch',
                             data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_batch_error_invalid_motor(self):
        data = {'motor': 'asd'}
        r = self.client.post(self.routeBase + '/batch',
                             data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_batch_error_invalid_distance(self):
        data = {'distance': 'asd'}
        r = self.client.post(self.routeBase + '/batch',
                             data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Correction routes
    def test_get_correction(self):
        route = self.routeBase + '/correction'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(float(r.json['correction']), 0.0)

    def test_post_correction(self):
        route = self.routeBase + '/correction'
        data = {'correction': 50.0}

        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_correction_error_not_float(self):
        route = self.routeBase + '/correction'

        data = {'correction': 50}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Angle routes
    def test_get_angle(self):
        route = self.routeBase + '/angle'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(float(r.json['angle']), 0.0)

    def test_post_angle(self):
        route = self.routeBase + '/angle'
        data = {'angle': 50.0}

        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_angle_error_angle_not_float(self):
        route = self.routeBase + '/angle'

        data = {'angle': 50}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Distance routes
    def test_get_distance(self):
        route = self.routeBase + '/distance'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(float(r.json['distance']), 0.0)

    def test_post_distance(self):
        route = self.routeBase + '/distance'
        data = {'distance': 50.0}

        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_distance_error_not_float(self):
        route = self.routeBase + '/distance'

        data = {'distance': 50}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Motor routes
    def test_get_motor(self):
        route = self.routeBase + '/motor'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json['motor'], False)

    def test_post_motor(self):
        route = self.routeBase + '/motor'
        data = {'motor': True}

        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_motor_error_not_bool(self):
        route = self.routeBase + '/motor'

        data = {'motor': 50}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Lock routes
    def test_post_lock_set_true(self):
        data = {'lock': True}
        route = self.routeBase + '/lock'
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_lock_set_false(self):
        data = {'lock': True}
        route = self.routeBase + '/lock'
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_get_lock_false(self):
        route = self.routeBase + '/lock'
        data = {'lock': False}
        self.client.post(route, data = json.dumps(data))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_get_lock_true(self):
        route = self.routeBase + '/lock'
        data = {'lock': True}
        self.client.post(route, data = json.dumps(data))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)


if __name__ == '__main__':
    unittest.main()
