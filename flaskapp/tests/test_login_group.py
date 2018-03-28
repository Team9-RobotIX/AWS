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


if __name__ == '__main__':
    unittest.main()
