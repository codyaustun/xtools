class MissingDataError(Exception):
    def __init__(self, course_id, db, collection, conditions = None):
        self.course_id = course_id
        self.db = db
        self.collection = collection
        self.conditions = conditions

    def __str__(self):
        return "No data for {0} in {1}".format(\
            self.course_id,
            self.collection)


class MissingStrategyError(Exception):
    def __init__(self, collection, catalog):
        self.collection = collection
        self.catalog = catalog

    def __str__(self):
        return "No strategy for creating {0}".format(\
            self.collection)