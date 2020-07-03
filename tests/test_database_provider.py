import unittest
from localshit.components.database_provider import Database
from localshit.components.ring import Ring
from localshit.components.election import Election

class TestDatabaseProvider(unittest.TestCase):
    def test_insert(self):
        database = Database()

        self.assertEqual(len(database.database), 0)
        database.insert("CO:12:Hello")
        database.insert("CO:11:Hello")
        self.assertEqual(len(database.database), 2)

    def test_get(self):
        database = Database()

        message = "CO:12:Hello"
        database.insert(message)
        entry = database.get("12")

        self.assertEqual(entry, message)

    def test_update(self):
        database = Database()

        message = "CO:12:Hello"
        database.insert(message)
        new_message = "CO:12:Hey"
        database.update(new_message)
        entry = database.get("12")

        self.assertEqual(entry, new_message)

    def test_get_duplicate(self):
        database = Database()

        message_1 = "CO:12:Hello"
        database.insert(message_1)
        message_2 = "CO:12:Hey"
        database.insert(message_2)
        entry = database.get("12")

        self.assertEqual(len(database.database), 1)
        self.assertEqual(entry, message_2)

    def test_count(self):
        database = Database()

        message_1 = "CO:12:Hello"
        message_2 = "CO:13:Hey"
        message_3 = "CO:14:Hi"
        database.insert(message_1)
        database.insert(message_2)
        database.insert(message_3)

        count = database.count()
        self.assertEqual(count, 3)

    def test_range_start(self):
        database = Database()

        message_1 = "CO:12:Hello"
        message_2 = "CO:13:Hey"
        message_3 = "CO:14:Hi"
        message_4 = "CO:15:Holla"
        database.insert(message_1)
        database.insert(message_2)
        database.insert(message_3)
        database.insert(message_4)

        ranges = database.get_range(start=-2)

        self.assertEqual(ranges[0], message_3)
        self.assertEqual(ranges[1], message_4)

    def test_range_start(self):
        database = Database()

        message_1 = "CO:12:Hello"
        message_2 = "CO:13:Hey"
        message_3 = "CO:14:Hi"
        message_4 = "CO:15:Holla"
        database.insert(message_1)
        database.insert(message_2)
        database.insert(message_3)
        database.insert(message_4)

        ranges = database.get_range(start=-10)
        self.assertEqual(len(ranges), 4)

    def test_delete(self):
        database = Database()

        self.assertEqual(len(database.database), 0)
        database.insert("CO:12:Hello")
        database.insert("CO:11:Hello")
        self.assertEqual(len(database.database), 2)
        database.delete("CO:11:Hello")
        self.assertEqual(len(database.database), 1)


