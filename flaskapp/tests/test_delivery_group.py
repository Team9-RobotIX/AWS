from flask_testing import TestCase
import json
import flaskapp
import dataset


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


