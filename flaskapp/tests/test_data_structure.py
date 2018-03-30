from flask_testing import TestCase
import unittest
import flaskapp


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
