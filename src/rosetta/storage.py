import pickle


class StorageObj:
    def __init__(self, db, *, key, get_default):
        self.key = key
        self.db = db

        if self.key in self.db:
            self.data = pickle.loads(db[key])
        else:
            self.data = get_default()

    def set(self, data):
        self.data = data

    def sync(self):
        self.db[self.key] = pickle.dumps(self.data)

    def get(self):
        return self.data
