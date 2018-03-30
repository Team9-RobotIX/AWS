from flask_testing import TestCase
import json
import unittest
import flaskapp
import dataset


class UsersGroupTest(TestCase):
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

    def register(self, username, password):
        data = {'username': username,
                'password': password}
        self.client.post(self.registerRoute, data = json.dumps(data))

    # Register route
    def test_get_users_empty(self):
        r = self.client.get('/users')
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [])

    def test_get_users_single(self):
        self.register('man', 'fooman')
        r = self.client.get('/users')
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [{"username": "man"}])

    def test_get_users_double(self):
        self.register('man', 'fooman')
        self.register('wookie', 'fiddle')
        r = self.client.get('/users')
        self.assertEquals(r.status_code, 200)
        self.assertEquals(r.json, [{"username": "man"},
                                   {"username": "wookie"}])


if __name__ == '__main__':
    unittest.main()
