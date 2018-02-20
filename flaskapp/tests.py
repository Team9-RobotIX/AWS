from flask_testing import TestCase
import json
import unittest
import flaskapp


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

    # Instruction routes
    def test_get_instruction(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        self.client.delete('/instructions')
        self.client.post('/instructions', data = json.dumps(data))

        for i in range(0, 3):
            route = '/instruction/' + str(i)
            r = self.client.get(route)
            self.assertEquals(r.status_code, 200)
            self.assertEquals(r.json, data[i])

    def test_get_instruction_invalid_index(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        self.client.delete('/instructions')
        self.client.post('/instructions', data = json.dumps(data))

        route = '/instruction/-1'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

        route = '/instruction/4'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

    def test_delete_instruction(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        self.client.delete('/instructions')
        self.client.post('/instructions', data = json.dumps(data))

        route = '/instruction/0'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 200)
        s = self.client.get('/instructions')
        self.assertEquals(s.status_code, 200)
        self.assertEquals(s.json, [data[1], data[2]])

    def test_delete_instruction_invalid_index(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        self.client.delete('/instructions')
        self.client.post('/instructions', data = json.dumps(data))

        route = '/instruction/-1'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 404)

        route = '/instruction/4'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 404)

        # Verify collection has not mutated
        s = self.client.get('/instructions')
        self.assertEquals(s.status_code, 200)
        self.assertEquals(s.json, data)

    # Correction routes
    def test_get_correction_none(self):
        route = '/correction'
        self.client.delete(route)

        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

    def test_get_correction_angle(self):
        route = '/correction'
        data = {'angle': 50.0}
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)

    def test_post_correction_angle(self):
        route = '/correction'
        data = {'angle': 50.0}
        self.client.delete(route)
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_correction_error_resubmit(self):
        route = '/correction'
        data = {'angle': 50.0}

        # Ensure a correction has already been issued
        self.client.post(route, data = json.dumps(data))

        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_correction_error_no_angle(self):
        route = '/correction'
        self.client.delete(route)

        data = {'foo': 50.0}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_correction_error_angle_not_float(self):
        route = '/correction'
        self.client.delete(route)

        data = {'angle': 50}
        r = self.client.post(route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_delete_correction_angle(self):
        route = '/correction'
        data = {'angle': 50.0}
        self.client.post(route, data = json.dumps(data))

        r = self.client.delete(route)
        self.assertEquals(r.status_code, 200)

    def test_delete_correction_error(self):
        route = '/correction'
        self.client.delete(route)  # Ensure correction is clear
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 404)

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
