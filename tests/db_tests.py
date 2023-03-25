import unittest
from db import db


class Tests(unittest.TestCase):
    def test_fetching(self):
        conn = db.get_connection()
        user = db.get_user(conn, 62863141)
        self.assertEqual(user.id, 62863141)  # add assertion here
        self.assertEqual(user.fullname, "Evgeny")


if __name__ == '__main__':
    unittest.main()
