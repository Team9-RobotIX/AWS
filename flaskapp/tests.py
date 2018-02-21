from flask_testing import TestCase
import json
import unittest
import flaskapp


class TargetGroupTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    # Targets route
    def test_get_targets_empty(self):
        route = '/targets'
        self.client.delete(route)

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_get_targets_single(self):
        route = '/targets'
        data = [{'name': 'Reception'}]
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data[0]))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        for i in range(0, len(r.json)):
            for k, v in data[i].iteritems():
                # ID assigned by server, so we don't check it
                if k != 'id':
                    self.assertEquals(v, data[i][k])

    def test_get_targets_multiple(self):
        route = '/targets'
        data = [{'name': 'Reception'},
                {'name': 'Pharmacy', 'description': 'foo'}]
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data[0]))
        self.client.post(route, data = json.dumps(data[1]))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        for i in range(0, len(r.json)):
            for k, v in data[i].iteritems():
                # ID assigned by server, so we don't check it
                if k != 'id':
                    self.assertEquals(v, data[i][k])

    def test_post_targets_name_and_color(self):
        route = '/targets'
        data = [{'name': 'Reception', 'color': 'red'}]
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data[0]))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        for i in range(0, len(r.json)):
            for k, v in data[i].itemitems():
                # ID assigned by server, so we don't check it
                if k != 'id':
                    self.assertEquals(v, data[i][k])

    def test_post_targets_name_and_description(self):
        route = '/targets'
        data = [{'name': 'Reception', 'description': 'foo'}]
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data[0]))

        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        for i in range(0, len(r.json)):
            for k, v in data[i].iteritems():
                # ID assigned by server, so we don't check it
                if k != 'id':
                    self.assertEquals(v, data[i][k])

    def test_post_targets_error_name(self):
        route = '/targets'
        data = [{'name': 7}]
        self.client.delete(route)
        r = self.client.post(route, data = json.dumps(data[0]))
        self.assertEquals(r.status_code, 400)

    def test_post_targets_error_no_name(self):
        route = '/targets'
        data = [{'description': 'foo'}]
        self.client.delete(route)
        r = self.client.post(route, data = json.dumps(data[0]))
        self.assertEquals(r.status_code, 400)

    def test_post_targets_error_description(self):
        route = '/targets'
        data = [{'name': 'ok', 'description': 5}]
        self.client.delete(route)
        r = self.client.post(route, data = json.dumps(data[0]))
        self.assertEquals(r.status_code, 400)

    def test_post_targets_error_color(self):
        route = '/targets'
        data = [{'name': 'ok', 'description': 'foo', 'color': 4}]
        self.client.delete(route)
        r = self.client.post(route, data = json.dumps(data[0]))
        self.assertEquals(r.status_code, 400)


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

    # Batch instructions route
    def test_get_instruction_batch(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        data_correction = {'angle': 10.3}
        self.client.delete('/instructions')
        self.client.delete('/correction')
        self.client.post('/instructions', data = json.dumps(data))
        self.client.post('/correction', data = json.dumps(data_correction))

        route = '/instructions/batch'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data,
                                   'correction': data_correction})

    def test_get_instruction_batch_no_correction(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        self.client.delete('/instructions')
        self.client.delete('/correction')
        self.client.post('/instructions', data = json.dumps(data))

        route = '/instructions/batch'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data})

    def test_get_instruction_batch_limit(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        data_correction = {'angle': 10.3}
        self.client.delete('/instructions')
        self.client.delete('/correction')
        self.client.post('/instructions', data = json.dumps(data))
        self.client.post('/correction', data = json.dumps(data_correction))

        route = '/instructions/batch?limit=2'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data[0:2],
                                   'correction': data_correction})

        route = '/instructions/batch?limit=3'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data,
                                   'correction': data_correction})

        route = '/instructions/batch?limit=10'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data,
                                   'correction': data_correction})

    def test_get_instruction_batch_limit_invalid(self):
        data = [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]
        data_correction = {'angle': 10.3}
        self.client.delete('/instructions')
        self.client.delete('/correction')
        self.client.post('/instructions', data = json.dumps(data))
        self.client.post('/correction', data = json.dumps(data_correction))

        route = '/instructions/batch?limit=0'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 400)

        route = '/instructions/batch?limit=-10'
        r = self.client.get(route)
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
