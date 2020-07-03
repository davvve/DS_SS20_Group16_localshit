"""
This class stores all quotes which are sent on the distributed system.
"""

from localshit.utils.utils import logging


class Database:
    def __init__(self):
        super(Database, self).__init__()
        self.database = []

    def insert(self, item):
        existing = False
        for entry in self.database:
            item_parts = item.split(":")
            parts = entry.split(":")
            if item_parts[1] == parts[1]:
                existing = True
                break
        if existing is True:
            self.update(item)
        else:
            self.database.append(item)
        logging.debug("Inserted %s. DB Size: %s" % (item, len(self.database)))

    def delete(self, item):
        if item in self.database:
            self.database.remove(item)

    def update(self, item):
        for index, entry in enumerate(self.database):
            item_parts = item.split(":")
            parts = entry.split(":")
            if item_parts[1] == parts[1]:
                self.database[index] = item

    def count(self):
        return len(self.database)

    def get(self, id):
        for entry in self.database:
            parts = entry.split(":")
            if id == parts[1]:
                return entry

    def get_at_position(self, index):
        return self.database[index]

    def get_range(self, start=None, end=None):
        try:
            if start and end:
                return self.database[start:end]
            elif start:
                return self.database[start:]
            elif end:
                return self.database[:end]
            else:
                return None
        except Exception as e:
            logging.error("Error at get_range: %s" % e)
