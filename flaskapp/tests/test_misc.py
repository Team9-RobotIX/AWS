from flask_testing import TestCase
import json
import unittest
import flaskapp


class MiscTest(TestCase):
    def create_app(self):
        self.app = flaskapp.app
        self.registerRoute = '/register'
        self.loginRoute = '/login'
        self.verifyRoute = '/verify'
        self.app.config['TESTING'] = True
        self.app.config['DATASET_DATABASE_URI'] = 'sqlite:///testdb.db'

        # 0: Vision
        # 1: App
        # 2: Verify (sender)
        # 3: Verify (receiver)
        self.POSSIBLE_STATES = ["IN_QUEUE", "MOVING_TO_SOURCE",
                                "AWAITING_AUTHENTICATION_SENDER",
                                "AWAITING_PACKAGE_LOAD",
                                "MOVING_TO_DESTINATION",
                                "AWAITING_AUTHENTICATION_RECEIVER",
                                "AWAITING_PACKAGE_RETRIEVAL",
                                "PACKAGE_RETRIEVAL_COMPLETE"]

        self.LEGAL_TRANSITIONS = {
            "IN_QUEUE": [("MOVING_TO_SOURCE", 0)],
            "MOVING_TO_SOURCE": [("AWAITING_AUTHENTICATION_SENDER", 0)],
            "AWAITING_AUTHENTICATION_SENDER": [("AWAITING_PACKAGE_LOAD", 2)],
            "AWAITING_PACKAGE_LOAD": [("PACKAGE_LOAD_COMPLETE", 1)],
            "PACKAGE_LOAD_COMPLETE": [("MOVING_TO_DESTINATION", 0)],
            "MOVING_TO_DESTINATION": [("AWAITING_AUTHENTICATION_RECEIVER", 0)],
            "AWAITING_AUTHENTICATION_RECEIVER": [("AWAITING_PACKAGE_RETRIEVAL",
                                                  3)],
            "AWAITING_PACKAGE_RETRIEVAL": [("PACKAGE_RETRIEVAL_COMPLETE", 1)],
            "PACKAGE_RETRIEVAL_COMPLETE": [("COMPLETE", 0)],
        }
        return self.app

    def setUp(self):
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

    def setup_delivery(self):
        data = [{
            'name': 'Blood sample',
            'description': 'Blood sample for patient Jane Doe',
            'priority': 0,
            'from': 1,
            'to': 2,
            'sender': 'foo',
            'receiver': 'foo2'
        }]
        bearer = self.login("foo", "bar")
        self.route = '/deliveries'
        r = self.client.post(self.route, data = json.dumps(data[0]),
                             headers = {"Authorization": "Bearer " + bearer})
        self.assertEquals(r.status_code, 200)
        return r.json['id']

    def login(self, username, password):
        self.route = '/login'
        r = self.client.post(self.route, data = json.dumps({
            "username": username,
            "password": password
        }))
        self.assertEquals(r.status_code, 200)
        return r.json['bearer']

    def patch_delivery(self, id, new_state, robot = 0):
        route = '/delivery/' + str(id)
        data = {
            "state": new_state,
            "robot": robot
        }
        return self.client.patch(route, data = json.dumps(data))

    def get_challenge_token(self, robot = 0):
        self.route = '/robot/' + str(robot) + '/batch'
        r = self.client.get(self.route)
        self.assertEquals(r.status_code, 200)

        if 'delivery' not in r.json:
            return ('', '')

        self.assertTrue('senderAuthToken' in r.json['delivery'])
        self.assertTrue('receiverAuthToken' in r.json['delivery'])

        senderToken = r.json['delivery']['senderAuthToken']
        receiverToken = r.json['delivery']['receiverAuthToken']
        self.assertEquals(len(senderToken), 10)
        self.assertEquals(len(senderToken), 10)
        return (senderToken, receiverToken)

    def verify_delivery_sender(self, id, robot = 0):
        bearer = self.login("foo", "bar")
        (token, _) = self.get_challenge_token(robot)
        r = self.execute_challenge(token, bearer, robot)
        return r

    def verify_delivery_receiver(self, id, robot = 0):
        bearer = self.login("foo2", "bar2")
        (_, token) = self.get_challenge_token(robot)
        r = self.execute_challenge(token, bearer, robot)
        return r

    def execute_challenge(self, token, bearer, robot = 0):
        self.route = '/robot/' + str(robot) + '/verify'
        headers = {'Authorization': 'Bearer ' + str(bearer)}
        data = {'token': token}
        r = self.client.post(self.route, data = json.dumps(data),
                             headers = headers)
        return r

    def create_delivery_and_legally_transition_to(self, state, robot):
        id = self.setup_delivery()
        currentState = "IN_QUEUE"

        while currentState != state:
            (targetState, mode) = self.LEGAL_TRANSITIONS[currentState][0]
            r = self.execute_transition(id, targetState, mode, robot)
            self.assertEquals(r.status_code, 200)
            route = '/delivery/' + str(id)
            r = self.client.get(route)
            self.assertEquals(r.json['state'], targetState)
            currentState = targetState

        return id

    def execute_transition(self, id, targetState, mode, robot):
        r = None
        if mode == 0:
            r = self.patch_delivery(id, targetState, robot)
        elif mode == 1:
            r = self.patch_delivery(id, targetState, robot)
        elif mode == 2:
            r = self.verify_delivery_sender(id, robot)
        elif mode == 3:
            r = self.verify_delivery_receiver(id, robot)

        return r

    def test_exception_handler(self):
        r = flaskapp.exception_handler("error")
        self.assertEqual(r[1], 500)
        self.assertEqual(r[0].json['code'], 500)
        self.assertEqual(r[0].json['error'], "Internal server error")
        self.assertEqual(r[0].json['friendly'], "error")

    def test_legal_transitions(self):
        robot = 0
        for state in self.POSSIBLE_STATES:
            id = self.create_delivery_and_legally_transition_to(state, robot)
            (targetState, mode) = self.LEGAL_TRANSITIONS[state][0]
            r = self.execute_transition(id, targetState, mode, robot)
            self.assertEquals(r.status_code, 200)
            robot += 1


if __name__ == '__main__':
    unittest.main()
