from flask_testing import TestCase
import json
import unittest
import flaskapp


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


if __name__ == '__main__':
    unittest.main()
