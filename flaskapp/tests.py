from flask_testing import TestCase
import json
import unittest
import flaskapp
import dataset


class LoginGroupTest(TestCase):
    def create_app(self):
        self.app = flaskapp.app
        self.registerRoute = '/register'
        self.loginRoute = '/login'
        self.app.config['TESTING'] = True
        self.app.config['DATASET_DATABASE_URI'] = 'sqlite:///testdb.db'
        return self.app

    def clear_database(self):
        db = dataset.connect(self.app.config['DATASET_DATABASE_URI'])
        db['users'].drop()

    # Register route
    def test_post_register(self):
        data = {'username': 'foo',
                'password': 'bar'}
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.data, '')

    def test_post_register_fail_no_username(self):
        data = {'password': 'bar'}
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_register_fail_no_password(self):
        data = {'password': 'bar'}
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_register_fail_empty(self):
        data = {}
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    # Login route
    def test_post_login(self):
        data = {'username': 'foo',
                'password': 'bar'}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        bearer1 = r.json['bearer']
        self.assertEquals(r.status_code, 200)
        self.assertEquals(len(bearer1), 32)

        r = self.client.post(self.loginRoute, data = json.dumps(data))
        bearer2 = r.json['bearer']
        self.assertEquals(r.status_code, 200)
        self.assertEquals(len(bearer2), 32)

        self.assertNotEquals(bearer1, bearer2)

    def test_post_login_fail_no_username(self):
        data = {'password': 'bar'}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_login_fail_no_password(self):
        data = {'password': 'bar'}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_login_fail_empty(self):
        data = {}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)


class DeliveryGroupTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    def create_dummy_targets(self):
        route = '/targets'
        data = [{'name': 'Reception'},
                {'name': 'Pharmacy', 'description': 'foo'}]
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data[0]))
        self.client.post(route, data = json.dumps(data[1]))

    def check_delivery_response_match(self, res, data):
        for k, v in res.iteritems():
            # ID assigned by server, so we don't check it
            if k != 'id' and k != 'state':
                if k == 'from' or k == 'to':
                    self.assertEquals(v['id'], data[k])
                else:
                    self.assertEquals(v, data[k])

    def setUp(self):
        self.route = '/deliveries'
        self.create_dummy_targets()
        self.client.delete(self.route)

    def add_data_single(self):
        self.data = [{
                    'name': 'Blood sample',
                    'description': 'Blood sample for patient Jane Doe',
                    'priority': 0,
                    'from': 1,
                    'to': 2
                    }]

    def add_data_multiple(self):
        self.data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2
        }, {
            'name': 'Papers',
            'description': 'Patient records',
            'priority': 0,
            'from': 2,
            'to': 1
        }]

    def add_data_triple(self):
        self.data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2
        }, {
            'name': 'Papers',
            'description': 'Patient records',
            'priority': 1,
            'from': 2,
            'to': 1
        }, {
            'name': 'Cake',
            'description': 'This was a triumph',
            'priority': 0,
            'from': 2,
            'to': 1
        }]

    def post_data_single(self):
        return self.client.post(self.route, data = json.dumps(self.data[0]))

    def post_data_multiple(self):
        self.client.post(self.route, data = json.dumps(self.data[0]))
        self.client.post(self.route, data = json.dumps(self.data[1]))

    def post_data_triple(self):
        self.client.post(self.route, data = json.dumps(self.data[0]))
        self.client.post(self.route, data = json.dumps(self.data[1]))
        self.client.post(self.route, data = json.dumps(self.data[2]))

    def check_response_in_range(self, r):
        for i in range(0, len(r.json)):
            self.check_delivery_response_match(r.json[i], self.data[i])

    # Deliveries route
    def test_get_deliveries_empty(self):
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_get_deliveries_single(self):
        self.add_data_single()
        self.post_data_single()

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_response_in_range(r)


    def test_get_deliveries_multiple(self):
        self.add_data_multiple()
        self.post_data_multiple()
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_response_in_range(r)

    def test_post_deliveries(self):
        self.add_data_single()
        r = self.post_data_single()
        self.assertEquals(r.status_code, 200)
        self.check_response_in_range(r)

    def test_post_deliveries_reordering(self):
        self.add_data_triple()
        self.post_data_triple()

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)

        # Order is 0, 2, 1
        self.check_delivery_response_match(r.json[0], self.data[0])
        self.check_delivery_response_match(r.json[1], self.data[2])
        self.check_delivery_response_match(r.json[2], self.data[1])

    def test_post_deliveries_no_description(self):
        self.add_data_single()
        r = self.post_data_single()
        self.assertEquals(r.status_code, 200)
        self.check_response_in_range(r)

    def test_post_deliveries_error_no_name(self):
        self.add_data_single()
        del self.data[0]['name'] #Remove name value from data
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_post_deliveries_error_name_not_string(self):
        self.add_data_single()
        self.data[0]['name'] = 1 #Set name value to some non-string val
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_post_deliveries_error_no_priority(self):
        self.add_data_single()
        del self.data[0]['priority'] #Remove priority value from data
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_post_deliveries_error_invalid_priority(self):
        self.add_data_single()
        self.data[0]['priority'] = None #Set priority value from data to None
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_delete_deliveries_empty(self):
        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 200)

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_delete_deliveries_single(self):
        self.add_data_single()
        self.post_data_single()

        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 200)

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_delete_deliveries_multiple(self):
        self.add_data_multiple()
        self.post_data_multiple()

        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 200)

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_post_deliveries_unique_id(self):
        self.add_data_multiple()
        self.post_data_multiple()

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertNotEquals(r.json[0]['id'], r.json[1]['id'])

    # Delivery routes
    def test_get_delivery(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = 'delivery/0'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_delivery_response_match(r.json, self.data[0])

    def test_get_delivery_error_invalid_key(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/a'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 404)

    def test_get_delivery_error_key_not_found(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/2'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 404)

    def test_patch_delivery(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = 'delivery/0'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json['state'], 'UNKNOWN')
        r = self.client.patch(self.route, data = json.dumps({"state":
                                                        "IN_PROGRESS"}))
        self.assertEquals(r.status_code, 200)

    def test_patch_delivery_error_invalid_key(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/foo'
        r = self.client.patch(self.route, data = json.dumps({"state":
                                                        "IN_PROGRESS"}))
        self.assertEquals(r.status_code, 404)

    def test_patch_delivery_error_key_not_found(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/2'
        r = self.client.patch(self.route, data = json.dumps({"state":
                                                        "IN_PROGRESS"}))
        self.assertEquals(r.status_code, 404)

    def test_delete_delivery(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/0'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 200)
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 404)

    def test_delete_delivery_error_invalid_key(self):
        self.route = '/delivery/foo'
        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 404)

    def test_delete_delivery_error_key_not_found(self):
        self.route = '/delivery/3'
        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 404)


class TargetGroupTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    def post_data_single(self, data):
        return self.client.post(self.route, data = json.dumps(data[0]))

    def post_data_multiple(self, data):
        self.client.post(self.route, data = json.dumps(data[0]))
        self.client.post(self.route, data = json.dumps(data[1]))

    def check_in_range_ignoring_id(self, r, data):
        for i in range(0, len(r.json)):
            for k, v in data[i].iteritems():
                # ID assigned by server, so we don't check it
                if k != 'id':
                    self.assertEquals(v, data[i][k])

    def setUp(self):
        self.route = '/targets'
        self.client.delete(self.route)

    # Targets route
    def test_get_targets_empty(self):
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_get_targets_single(self):
        data = [{'name': 'Reception'}]
        self.post_data_single(data)
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_in_range_ignoring_id(r, data)

    def test_get_targets_multiple(self):
        data = [{'name': 'Reception'},
                {'name': 'Pharmacy', 'description': 'foo'}]
        self.post_data_multiple(data)
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_in_range_ignoring_id(r, data)

    def test_post_targets_name_and_color(self):
        data = [{'name': 'Reception', 'color': 'red'}]
        self.post_data_single(data)
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_in_range_ignoring_id(r, data)

    def test_post_targets_name_and_description(self):
        data = [{'name': 'Reception', 'description': 'foo'}]
        self.post_data_single(data)
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.check_in_range_ignoring_id(r, data)

    def test_post_targets_error_name(self):
        data = [{'name': 7}]
        r = self.post_data_single(data)
        self.assertEquals(r.status_code, 400)

    def test_post_targets_error_no_name(self):
        data = [{'description': 'foo'}]
        r = self.post_data_single(data)
        self.assertEquals(r.status_code, 400)

    def test_post_targets_error_description(self):
        data = [{'name': 'ok', 'description': 5}]
        r = self.post_data_single(data)
        self.assertEquals(r.status_code, 400)

    def test_post_targets_error_color(self):
        data = [{'name': 'ok', 'description': 'foo', 'color': 4}]
        r = self.post_data_single(data)
        self.assertEquals(r.status_code, 400)


    # Target route

    def check_repsonse_in_range(self, r, data, index):
        for k, v in data[index].iteritems():
            self.assertEquals(v, r.json[k])

    def get_default_data(self):
        return [{'name': 'ok', 'description': 'bar'},
                {'name': 'Pharmacy', 'description': 'foo'}]

    def test_get_target(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))
        self.client.post('/targets', data = json.dumps(data[1]))

        route = '/target/1'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.check_repsonse_in_range(r, data, 0)

        route = '/target/2'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.check_repsonse_in_range(r, data, 1)

    def test_get_target_error_invalid_index(self):
        self.client.delete('/targets')

        route = '/target/1'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

        route = '/target/-1'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

    def test_get_target_error_index_numeric(self):
        self.client.delete('/targets')
        route = '/target/a'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)


    def test_patch_target(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))

        route = '/target/1'
        data2 = {'color': 'red'}
        r = self.client.patch(route, data = json.dumps(data2))
        self.assertEquals(r.status_code, 200)
        for k, v in data[1].iteritems():
            self.assertEquals(v, data[1][k])
        self.assertEquals(r.json['color'], 'red')

    def test_patch_target_error_invalid_color(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))

        route = '/target/1'
        data2 = {'color': 2.0}
        r = self.client.patch(route, data = json.dumps(data2))
        self.assertEquals(r.status_code, 400)

    def test_patch_target_error_invalid_index(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))

        route = '/target/-1'
        data2 = {'color': 'red'}
        r = self.client.patch(route, data = json.dumps(data2))
        self.assertEquals(r.status_code, 404)

    def test_patch_target_error_index_numeric(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))

        route = '/target/a'
        data2 = {'color': 'red'}
        r = self.client.patch(route, data = json.dumps(data2))
        self.assertEquals(r.status_code, 404)

    def test_delete_target(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))
        self.client.post('/targets', data = json.dumps(data[1]))

        route = '/target/1'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 200)

    def test_delete_target_error_invalid_index(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))
        self.client.post('/targets', data = json.dumps(data[1]))

        route = '/target/3'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 404)

        route = '/target/-1'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 404)

    def test_delete_target_error_index_numeric(self):
        data = self.get_default_data()
        self.client.delete('/targets')
        self.client.post('/targets', data = json.dumps(data[0]))
        self.client.post('/targets', data = json.dumps(data[1]))

        route = '/target/a'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 404)


class RobotGroupTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    def setUp(self):
        self.route = '/instructions'
        self.client.delete(self.route)

    def data_double(self):
        return [{'type': 'MOVE', 'value': 100}, {'type': 'TURN', 'value': 90}]

    def data_single(self):
        return {'type': 'MOVE', 'value': 100}


    # Instruction routes
    def test_delete_instructions(self):
        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 200)

    def test_get_instructions_queue_empty(self):
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_get_instructions(self):
        data = self.data_double()
        self.client.post(self.route, data = json.dumps(data))

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_instructions_single(self):
        data = self.data_single()
        r = self.client.post(self.route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [data])

    def test_post_instructions_multiple(self):
        data = self.data_double()
        r = self.client.post(self.route, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, data)

    def test_post_instructions_fails_with_missing_type(self):
        data = [{'value': 100}]
        r = self.client.post(self.route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_instructions_fails_with_missing_value(self):
        data = [{'type': 'MOVE'}]
        r = self.client.post(self.route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_instructions_fails_with_invalid_type(self):
        data = [{'type': 'HALT', 'value': 100}]
        r = self.client.post(self.route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_instructions_fails_with_bad_angle(self):
        data = [{'type': 'TURN', 'value': 190.0}]
        r = self.client.post(self.route, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)


    # Batch instructions route
    def batch_data(self):
        return [{'type': 'MOVE', 'value': 100},
                {'type': 'TURN', 'value': 90},
                {'type': 'TURN', 'value': -90}]

    def delete_instructions_and_corrections(self):
        self.client.delete('/instructions')
        self.client.delete('/correction')

    def test_get_instruction_batch(self):
        data = self.batch_data()
        data_correction = {'angle': 10.3}
        self.delete_instructions_and_corrections()
        self.client.post('/instructions', data = json.dumps(data))
        self.client.post('/correction', data = json.dumps(data_correction))

        route = '/instructions/batch'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data,
                                   'correction': data_correction})

    def test_get_instruction_batch_no_correction(self):
        data = self.batch_data()
        self.delete_instructions_and_corrections()
        self.client.post('/instructions', data = json.dumps(data))

        route = '/instructions/batch'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, {'instructions': data})

    def test_get_instruction_batch_limit(self):
        data = self.batch_data()
        data_correction = {'angle': 10.3}
        self.delete_instructions_and_corrections()
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
        data = self.batch_data()
        data_correction = {'angle': 10.3}
        self.delete_instructions_and_corrections()
        self.client.post('/instructions', data = json.dumps(data))
        self.client.post('/correction', data = json.dumps(data_correction))

        route = '/instructions/batch?limit=0'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 400)

        route = '/instructions/batch?limit=-10'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 400)

    # Instruction routes
    def delete_and_post_instructions(self, data):
        self.client.delete('/instructions')
        self.client.post('/instructions', data = json.dumps(data))

    def test_get_instruction(self):
        data = self.batch_data()
        self.delete_and_post_instructions(data)

        for i in range(0, 3):
            route = '/instruction/' + str(i)
            r = self.client.get(route)
            self.assertEquals(r.status_code, 200)
            self.assertEquals(r.json, data[i])

    def test_get_instruction_invalid_index(self):
        data = self.batch_data()
        self.delete_and_post_instructions(data)

        route = '/instruction/-1'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

        route = '/instruction/4'
        r = self.client.get(route)
        self.assertEquals(r.status_code, 404)

    def test_delete_instruction(self):
        data = self.batch_data()
        self.delete_and_post_instructions(data)

        route = '/instruction/0'
        r = self.client.delete(route)
        self.assertEquals(r.status_code, 200)
        s = self.client.get('/instructions')
        self.assertEquals(s.status_code, 200)
        self.assertEquals(s.json, [data[1], data[2]])

    def test_delete_instruction_invalid_index(self):
        data = self.batch_data()
        self.delete_and_post_instructions(data)

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

    def test_delivery_init(self):
        t1 = flaskapp.Target(1, "Reception")
        t2 = flaskapp.Target(2, "Office")

        # Delivery can be initialised without errors
        flaskapp.Delivery(1, t1, t2, 0, "Foo", "Bar")

        # Delivery with no packages raises an error
        with self.assertRaises(ValueError):
            flaskapp.Delivery(1, t1, t2, 0, "Foo", "Bar",
                              5, 20.0,
                              19.0)

        with self.assertRaises(ValueError):
            flaskapp.Delivery(1, t1, t2, 0, "Foo", "Bar",
                              5, 20.0,
                              21.0, -1)


if __name__ == '__main__':
    unittest.main()
