from flask_testing import TestCase
import json
import unittest
import flaskapp
import dataset


class MiscTest(TestCase):
    def create_app(self):
        self.app = flaskapp.app
        self.app.config['TESTING'] = True
        self.app.config['DATASET_DATABASE_URI'] = 'sqlite:///testdb.db'
        return self.app

    def test_exception_handler(self):
        r = flaskapp.exception_handler("error")
        self.assertEqual(r[1], 500)
        self.assertEqual(r[0]['code'], 500)
        self.assertEqual(r[0]['error'], "Internal server error")
        self.assertEqual(r[0]['friendly'], "error")


class MiscTestProduction(TestCase):
    def create_app(self):
        self.app = flaskapp.app
        self.app.config['TESTING'] = False
        self.app.config['DATASET_DATABASE_URI'] = 'sqlite:///testdb.db'
        return self.app

    def test_exception_handler(self):
        r = flaskapp.exception_handler("error")
        r = flaskapp.exception_handler("error")
        self.assertEqual(r[1], 500)
        self.assertEqual(r[0]['code'], 500)
        self.assertEqual(r[0]['error'], "Internal server error")
        self.assertEqual(r[0]['friendly'], "Internal server error. " +
                         "Error messages are suppressed in production mode.")


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

    def setUp(self):
        self.clear_database()

    def register_foo(self):
        data = {'username': 'foo',
                'password': 'bar'}
        self.client.post(self.registerRoute, data = json.dumps(data))

    # Register route
    def test_post_register(self):
        data = {'username': 'foo',
                'password': 'bar'}
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.data, '')

    def test_post_register_fail_already_exists(self):
        data = {'username': 'foo',
                'password': 'bar'}
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 200)
        r = self.client.post(self.registerRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

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
        self.register_foo()
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

    def test_post_login_fail_wrong_combination(self):
        self.register_foo()
        data = {'username': 'INEXISTENTUSER',
                'password': 'WRONGPASSWORD'}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 401)

    def test_post_login_fail_no_username(self):
        self.register_foo()
        data = {'password': 'bar'}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_login_fail_no_password(self):
        self.register_foo()
        data = {'password': 'bar'}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)

    def test_post_login_fail_empty(self):
        self.register_foo()
        data = {}
        r = self.client.post(self.loginRoute, data = json.dumps(data))
        self.assertEquals(r.status_code, 400)


class DeliveryGroupTest(TestCase):
    def create_app(self):
        self.app = flaskapp.app
        self.registerRoute = '/register'
        self.loginRoute = '/login'
        self.verifyRoute = '/verify'
        self.app.config['TESTING'] = True
        self.app.config['DATASET_DATABASE_URI'] = 'sqlite:///testdb.db'
        return self.app

    def clear_database(self):
        db = dataset.connect(self.app.config['DATASET_DATABASE_URI'])
        db['users'].drop()

    def setUp(self):
        self.clear_database()
        self.route = '/deliveries'
        self.client.delete(self.route)
        self.create_dummy_targets()
        self.client.delete(self.route)
        self.register_foo_and_foo2()

        loginData = {'username': 'foo', 'password': 'bar'}
        r = self.client.post('/login', data = json.dumps(loginData))
        self.headers = {'Authorization': 'Bearer ' + str(r.json['bearer'])}

    def register_foo_and_foo2(self):
        data = {'username': 'foo',
                'password': 'bar'}
        self.client.post(self.registerRoute, data = json.dumps(data))
        data = {'username': 'foo2',
                'password': 'bar2'}
        self.client.post(self.registerRoute, data = json.dumps(data))

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

    def add_data_single(self):
        self.data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2,
            'sender': 'foo',
            'receiver': 'foo2'
        }]

    def add_data_multiple(self):
        self.data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2,
            'sender': 'foo',
            'receiver': 'foo2'
        }, {
            'name': 'Papers',
            'description': 'Patient records',
            'priority': 0,
            'from': 2,
            'to': 1,
            'sender': 'foo',
            'receiver': 'foo2'
        }]

    def add_data_triple(self):
        self.data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2,
            'sender': 'foo',
            'receiver': 'foo2'
        }, {
            'name': 'Papers',
            'description': 'Patient records',
            'priority': 1,
            'from': 2,
            'to': 1,
            'sender': 'foo',
            'receiver': 'foo2'
        }, {
            'name': 'Cake',
            'description': 'This was a triumph',
            'priority': 0,
            'from': 2,
            'to': 1,
            'sender': 'foo',
            'receiver': 'foo2'
        }]

    def post_data_single(self):
        return self.client.post(self.route, data = json.dumps(self.data[0]),
                                headers = self.headers)

    def post_data_multiple(self):
        self.client.post(self.route, data = json.dumps(self.data[0]),
                         headers = self.headers)
        self.client.post(self.route, data = json.dumps(self.data[1]),
                         headers = self.headers)

    def post_data_triple(self):
        self.client.post(self.route, data = json.dumps(self.data[0]),
                         headers = self.headers)
        self.client.post(self.route, data = json.dumps(self.data[1]),
                         headers = self.headers)
        self.client.post(self.route, data = json.dumps(self.data[2]),
                         headers = self.headers)

    def check_response_in_range(self, r):
        for i in range(0, len(r.json)):
            self.check_delivery_response_match(r.json[i], self.data[i])

    def simulate_delivery_state_changes(self, finalState, robotId, deliveryId):
        states = ["MOVING_TO_SOURCE", "AWAITING_AUTHENTICATION_SENDER",
                  "AWAITING_PACKAGE_LOAD", "PACKAGE_LOAD_COMPLETE",
                  "MOVING_TO_DESTINATION", "AWAITING_AUTHENTICATION_RECEIVER",
                  "AWAITING_PACKAGE_RETRIEVAL", "PACKAGE_RETRIEVAL_COMPLETE",
                  "COMPLETE"]
        for s in states[:states.index(finalState) + 1]:
            self.change_delivery_state(s, robotId, deliveryId)

    def change_delivery_state(self, state, robotId, deliveryId):
        route = '/delivery/' + str(deliveryId)
        r = self.client.patch(route, data = json.dumps({
            "state": state,
            "robot": robotId
        }))
        self.assertEquals(r.status_code, 200)

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
        self.check_delivery_response_match(r.json, self.data[0])

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
        self.check_delivery_response_match(r.json, self.data[0])

    def test_post_deliveries_error_no_name(self):
        self.add_data_single()
        del self.data[0]['name']
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_post_deliveries_error_name_not_string(self):
        self.add_data_single()
        self.data[0]['name'] = 1
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_post_deliveries_error_no_priority(self):
        self.add_data_single()
        del self.data[0]['priority']
        r = self.post_data_single()
        self.assertEquals(r.status_code, 400)

    def test_post_deliveries_error_invalid_priority(self):
        self.add_data_single()
        self.data[0]['priority'] = None
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

    def test_delete_deliveries_clears_all_assignments(self):
        self.add_data_triple()
        deliveries = []

        # Assign robots to deliveries
        for id in range(0, 3):
            route = '/deliveries'
            r = self.client.post(route, data = json.dumps(self.data[id]),
                                 headers = self.headers)
            self.assertEquals(r.status_code, 200)
            delivery_id = r.json['id']
            deliveries.append(delivery_id)

            route = '/delivery/' + str(delivery_id)
            r = self.client.patch(route, data = json.dumps({
                "state": "MOVING_TO_SOURCE",
                "robot": id
            }))
            self.assertEquals(r.status_code, 200)

            route = '/robot/' + str(id) + '/batch'
            r = self.client.get(route)
            self.assertEquals(r.status_code, 200)
            self.assertTrue('delivery' in r.json)

        # Run delete on deliveries
        r = self.client.delete(self.route)
        self.assertEquals(r.status_code, 200)

        # Check the robots have been deassigned
        for id in range(0, 3):
            route = '/robot/' + str(id) + '/batch'
            r = self.client.get(route)
            self.assertEquals(r.status_code, 200)
            self.assertTrue('delivery' not in r.json)

    def test_post_deliveries_unique_id(self):
        self.add_data_multiple()
        self.post_data_multiple()

        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertNotEquals(r.json[0]['id'], r.json[1]['id'])

    def test_post_deliveries_error_wrong_token(self):
        self.add_data_single()
        r = self.client.post(self.route, data = json.dumps(self.data[0]),
                             headers = {'Authorization': 'Bearer VOID'})
        self.assertEquals(r.status_code, 401)

    # Delivery routes
    def test_get_delivery(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/0'
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

        self.route = '/delivery/0'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json['state'], 'IN_QUEUE')
        r = self.client.patch(self.route, data = json.dumps(
            {"state": "MOVING_TO_SOURCE", "robot": 0}))
        self.assertEquals(r.status_code, 200)
        self.assertTrue('state' in r.json)
        self.assertTrue('robot' in r.json)
        self.assertEquals(r.json['state'], 'MOVING_TO_SOURCE')
        self.assertEquals(r.json['robot'], 0)

        # Check that robot was assigned this delivery
        self.route = '/robot/0/batch'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' in r.json)
        self.assertTrue('senderAuthToken' in r.json['delivery'])
        self.assertTrue('receiverAuthToken' in r.json['delivery'])
        self.assertTrue('state' in r.json['delivery'])
        self.assertEquals(r.json['delivery']['state'], "MOVING_TO_SOURCE")

    def test_patch_delivery_syncs_with_robot(self):
        self.add_data_single()
        r = self.post_data_single()
        self.assertEquals(r.status_code, 200)
        self.simulate_delivery_state_changes("MOVING_TO_SOURCE",
                                             0, 0)

        r = self.client.get('/delivery/0')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('robot' in r.json, 0)
        self.assertEquals(r.json['robot'], 0)

        r = self.client.get('/robot/0/batch')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' in r.json)
        self.assertTrue('state' in r.json['delivery'])
        self.assertEquals(r.json['delivery']['state'], "MOVING_TO_SOURCE")

        r = self.client.patch('/delivery/0', data = json.dumps(
            {"state": "AWAITING_AUTHENTICATION_SENDER"}))
        self.assertEquals(r.status_code, 200)

        r = self.client.get('/delivery/0')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('robot' in r.json, 0)
        self.assertEquals(r.json['robot'], 0)

        r = self.client.get('/robot/0/batch')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' in r.json)
        self.assertTrue('state' in r.json['delivery'])
        self.assertEquals(r.json['delivery']['state'],
                          "AWAITING_AUTHENTICATION_SENDER")

    def test_patch_delivery_to_complete_clears_robot_assignment(self):
        self.add_data_single()
        r = self.post_data_single()
        self.assertEquals(r.status_code, 200)
        self.simulate_delivery_state_changes("PACKAGE_RETRIEVAL_COMPLETE",
                                             0, 0)

        r = self.client.get('/robot/0/batch')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' in r.json)

        r = self.client.patch('/delivery/0', data = json.dumps({
            "state": "COMPLETE"}))
        self.assertEquals(r.status_code, 200)

        r = self.client.get('/robot/0/batch')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' not in r.json)

    def test_patch_delivery_error_robot_occupied(self):
        self.add_data_multiple()
        self.post_data_multiple()  # 0 and 1

        self.simulate_delivery_state_changes("MOVING_TO_SOURCE",
                                             0, 0)
        r = self.client.get('/robot/0/batch')
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' in r.json)

        r = self.client.patch('/delivery/1', data = json.dumps({
            "state": "MOVING_TO_SOURCE", "robot": 0}))
        self.assertEquals(r.status_code, 400)

    def test_patch_delivery_error_invalid_state(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/0'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json['state'], 'IN_QUEUE')
        r = self.client.patch(self.route, data = json.dumps(
            {"state": "FOOBAR"}))
        self.assertEquals(r.status_code, 400)

    def test_patch_delivery_error_invalid_key(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/foo'
        r = self.client.patch(self.route, data = json.dumps(
            {"state": "MOVING_TO_SOURCE"}))
        self.assertEquals(r.status_code, 404)

    def test_patch_delivery_error_key_not_found(self):
        self.add_data_multiple()
        self.post_data_multiple()

        self.route = '/delivery/2'
        r = self.client.patch(self.route, data = json.dumps(
            {"state": "MOVING_TO_SOURCE"}))
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

    def test_delete_delivery_assigned_to_robot_clears_assignment(self):
        self.add_data_triple()
        deliveries = []

        # Assign robots to deliveries
        for id in range(0, 3):
            route = '/deliveries'
            r = self.client.post(route, data = json.dumps(self.data[id]),
                                 headers = self.headers)
            self.assertEquals(r.status_code, 200)
            delivery_id = r.json['id']
            deliveries.append(delivery_id)

            route = '/delivery/' + str(delivery_id)
            r = self.client.patch(route, data = json.dumps({
                "state": "MOVING_TO_SOURCE",
                "robot": id
            }))
            self.assertEquals(r.status_code, 200)

            route = '/robot/' + str(id) + '/batch'
            r = self.client.get(route)
            self.assertEquals(r.status_code, 200)
            self.assertTrue('delivery' in r.json)

        # Run delete on deliveries and check the robots have been deassigned
        for id in range(0, 3):
            route = '/delivery/' + str(id)
            r = self.client.delete(route)
            self.assertEquals(r.status_code, 200)
            route = '/robot/' + str(id) + '/batch'
            r = self.client.get(route)
            self.assertEquals(r.status_code, 200)
            self.assertTrue('delivery' not in r.json)

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


class VerifyTest(TestCase):
    def create_app(self):
        self.app = flaskapp.app
        self.registerRoute = '/register'
        self.loginRoute = '/login'
        self.verifyRoute = '/verify'
        self.app.config['TESTING'] = True
        self.app.config['DATASET_DATABASE_URI'] = 'sqlite:///testdb.db'
        return self.app

    def clear_database(self):
        db = dataset.connect(self.app.config['DATASET_DATABASE_URI'])
        db['users'].drop()

    def setUp(self):
        self.clear_database()
        self.route = '/deliveries'
        self.client.delete(self.route)
        r = self.client.get(self.route)
        self.assertEquals(r.json, [])

        for i in range(0, 5):
            route = '/robot/' + str(i) + '/batch'
            r = self.client.get(route)
            self.assertTrue('delivery' not in r.json)

        self.create_dummy_targets()
        self.register_foo_and_foo2()

        loginData = {'username': 'foo', 'password': 'bar'}
        r = self.client.post('/login', data = json.dumps(loginData))
        self.headers = {'Authorization': 'Bearer ' + str(r.json['bearer'])}

    def register_foo_and_foo2(self):
        data = {'username': 'foo',
                'password': 'bar'}
        self.client.post(self.registerRoute, data = json.dumps(data))
        data = {'username': 'foo2',
                'password': 'bar2'}
        self.client.post(self.registerRoute, data = json.dumps(data))

    def create_dummy_targets(self):
        route = '/targets'
        data = [{'name': 'Reception'},
                {'name': 'Pharmacy', 'description': 'foo'}]
        self.client.delete(route)
        self.client.post(route, data = json.dumps(data[0]))
        self.client.post(route, data = json.dumps(data[1]))

    def add_data_single(self):
        self.data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2,
            'sender': 'foo',
            'receiver': 'foo2'
        }]

    def setup_delivery(self):
        self.add_data_single()
        bearer = self.login("foo", "bar")
        self.route = '/deliveries'
        r = self.client.post(self.route, data = json.dumps(self.data[0]),
                             headers = {"Authorization": "Bearer " + bearer})
        self.assertEquals(r.status_code, 200)

    def simulate_delivery_state_changes(self, finalState):
        states = ["MOVING_TO_SOURCE", "AWAITING_AUTHENTICATION_SENDER",
                  "AWAITING_PACKAGE_LOAD", "PACKAGE_LOAD_COMPLETE",
                  "MOVING_TO_DESTINATION", "AWAITING_AUTHENTICATION_RECEIVER",
                  "AWAITING_PACKAGE_RETRIEVAL", "PACKAGE_RETRIEVAL_COMPLETE",
                  "COMPLETE"]
        for s in states[:states.index(finalState) + 1]:
            self.change_delivery_state(s)

    def change_delivery_state(self, state):
        self.route = '/delivery/0'
        r = self.client.patch(self.route, data = json.dumps({
            "state": state,
            "robot": 0
        }))
        self.assertEquals(r.status_code, 200)

    def login(self, username, password):
        self.route = '/login'
        r = self.client.post(self.route, data = json.dumps({
            "username": username,
            "password": password
        }))
        self.assertEquals(r.status_code, 200)
        return r.json['bearer']

    def get_challenge_token(self):
        self.route = '/robot/0/batch'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)

        self.assertTrue('delivery' in r.json)
        self.assertTrue('senderAuthToken' in r.json['delivery'])
        self.assertTrue('receiverAuthToken' in r.json['delivery'])

        senderToken = r.json['delivery']['senderAuthToken']
        receiverToken = r.json['delivery']['receiverAuthToken']
        self.assertEquals(len(senderToken), 10)
        self.assertEquals(len(senderToken), 10)
        return (senderToken, receiverToken)

    def execute_challenge(self, token, bearer):
        self.route = '/robot/0/verify'
        headers = {'Authorization': 'Bearer ' + str(bearer)}
        data = {'token': token}
        r = self.client.post(self.route, data = json.dumps(data),
                             headers = headers)
        return r

    def test_post_verify_auth_sender(self):
        self.setup_delivery()
        self.simulate_delivery_state_changes("AWAITING_AUTHENTICATION_SENDER")
        bearer = self.login("foo", "bar")
        (token, _) = self.get_challenge_token()
        r = self.execute_challenge(token, bearer)
        self.assertEquals(r.status_code, 200)

        self.route = "/delivery/0"
        r = self.client.get(self.route)
        self.assertEquals(r.json['state'], "AWAITING_PACKAGE_LOAD")

    def test_post_verify_auth_receiver(self):
        self.setup_delivery()
        self.simulate_delivery_state_changes(
            "AWAITING_AUTHENTICATION_RECEIVER")
        bearer = self.login("foo2", "bar2")
        (_, token) = self.get_challenge_token()
        r = self.execute_challenge(token, bearer)
        self.assertEquals(r.status_code, 200)

        self.route = "/delivery/0"
        r = self.client.get(self.route)
        self.assertEquals(r.json['state'], "AWAITING_PACKAGE_RETRIEVAL")

    def test_post_verify_error_wrong_state(self):
        self.setup_delivery()
        self.route = '/robot/0/batch'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' not in r.json)

    def test_post_verify_error_wrong_token(self):
        self.setup_delivery()
        self.simulate_delivery_state_changes(
            "AWAITING_AUTHENTICATION_SENDER")
        bearer = self.login("foo2", "bar2")
        token = "blahblah"
        r = self.execute_challenge(token, bearer)
        self.assertEquals(r.status_code, 401)

    def test_post_verify_error_wrong_bearer(self):
        self.setup_delivery()
        self.simulate_delivery_state_changes(
            "AWAITING_AUTHENTICATION_SENDER")
        bearer = "foofoo"
        (_, token) = self.get_challenge_token()
        r = self.execute_challenge(token, bearer)
        self.assertEquals(r.status_code, 401)


class DataStructureTest(TestCase):
    def create_app(self):
        app = flaskapp.app
        app.config['TESTING'] = True
        return app

    def test_delivery_init(self):
        t1 = flaskapp.Target(1, "Reception")
        t2 = flaskapp.Target(2, "Office")

        # Delivery can be initialised without errors
        flaskapp.Delivery(1, t1, t2, 0, "Foo", "Bar", "jdoe", "drseuss")

        # Delivery with no packages raises an error
        with self.assertRaises(ValueError):
            flaskapp.Delivery(1, t1, t2, 0, "Foo", "Bar",
                              "jdoe", "drseuss", 5, 20.0, 19.0)

        with self.assertRaises(ValueError):
            flaskapp.Delivery(1, t1, t2, 0, "Foo", "Bar",
                              "jdoe", "drseuss", 5, 20.0, 21.0, -1)


if __name__ == '__main__':
    unittest.main()
