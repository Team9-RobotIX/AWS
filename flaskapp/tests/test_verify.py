from flask_testing import TestCase
import json
import unittest
import flaskapp
import dataset


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

    def test_post_verify_error_robot_not_delivering(self):
        self.setup_delivery()

        self.route = '/robot/0/batch'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' not in r.json)

        bearer = self.login("foo", "bar")
        r = self.execute_challenge('dummy', bearer)
        self.assertEquals(r.status_code, 400)

    def test_post_verify_error_wrong_state(self):
        self.setup_delivery()
        self.simulate_delivery_state_changes("MOVING_TO_SOURCE")

        self.route = '/robot/0/batch'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)
        self.assertTrue('delivery' in r.json)

        bearer = self.login("foo", "bar")
        (_, token) = self.get_challenge_token()
        r = self.execute_challenge(token, bearer)
        self.assertEquals(r.status_code, 400)

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


if __name__ == '__main__':
    unittest.main()
