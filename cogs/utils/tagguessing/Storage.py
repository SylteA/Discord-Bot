import json


class Storage:
    def __init__(self, fname=r'cogs\tagguessing\bot_storage.json'):
        self.fname = fname
        self.data = None
        self.grab()

    def grab(self):
        try:
            with open(self.fname, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            with open(self.fname, 'w') as f:
                json.dump(dict(), f)
            data = dict()
        self.data = data


    def write(self):
        with open(self.fname, 'w') as f:
            json.dump(self.data, f)

    def add(self, key, item):
        self.data[key] = item
        self.write()

    def append(self, key, item):
        if key in self.data:
            self.data[key].append(item)
            self.write()
        else:
            print('key not found')

    def dict_add(self, id, key, item):
        if id not in self.data:
            self.add(id, dict())
        self.data[id][key] = item
        self.write()

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            self.write()
        else:
            print('key not found')

    def dict_delete(self, id, key):
        if id in self.data:
            if key in self.data[id]:
                del self.data[id][key]
            else:
                print('key not found')
        else:
            print('id not found')

    def load_tags(self):
        # This needs to be updated to grab from database
        return {"hello": 'Hello! How are you', "bye": 'Have a good night!'}

