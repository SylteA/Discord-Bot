from pymongo import MongoClient
import datetime
import pandas as pd


class DataBase:
    def __init__(self):
        self.client = MongoClient("")
        self.users = self.client.heroku_2d7ckb75.users
        self.logs = self.client.heroku_2d7ckb75.logs
        self.stats = self.client.heroku_2d7ckb75.server_stats

    def update_messages(self, user, msgs=1):
        try:
            id = self.get_usr(self.users, user)["_id"]
        except:
            id = None
        old, date = self.get_msgs(user)
        if id != None:
            self.users.find_one_and_update({"_id":id}, {"$set":{"messages": old + msgs}})
        else:
            self.create_new_messages(user, 1)

    def get_msgs(self, usr):
        try:
            u = self.get_usr(self.users, usr)
            return u["messages"], u["joined"]
        except:
            return 0, self.get_date()

    def create_new_messages(self, user, msgs=0):
        usr = {"user": str(user), "messages": msgs, "joined":DataBase.get_date()}
        id = self.users.insert_one(usr).inserted_id
        return id

    def get_usr(self, db, user):
        found = db.find_one({"user":str(user)})
        return found

    def update_server_stats(self,usr=0):
        try:
            if usr == 1:
                old = self.stats.find_one({"date": DataBase.get_date()})["newUsers"]
                self.stats.find_one_and_update({"date": DataBase.get_date()}, {"$set": {"newUsers": old + 1}})
            else:
                old = self.stats.find_one({"date":DataBase.get_date()})["messages"]
                self.stats.find_one_and_update({"date": DataBase.get_date()}, {"$set": {"messages": old + 1}})
        except:
            stat = {"date": DataBase.get_date(), "messages": 1, "newUsers": 0}
            id = self.stats.insert_one(stat).inserted_id

    def get_top_users(self):
        query = self.users.find({})
        top = 0
        users = []
        for doc in query:
            if doc["messages"] > top:
                top = doc["messages"]
                users = [doc["user"]]
            elif doc["messages"] == top:
                users.append(doc["user"])

        return users, top

    def get_all_messages(self):
        query = self.stats.find({})
        sum = 0
        l = 0
        for doc in query:
            l += 1
            sum += doc["messages"]

        return sum, l

    def scoreboard(self):
        query = self.users.find({})
        usrs = []
        for doc in query:
            msg = int(doc["messages"])
            usrs.append([doc["user"], msg])
        usrs.sort(key=lambda x: x[1])
        usrs = usrs[-5:]

        df = pd.DataFrame(usrs, columns=["user", "messages"])
        d = df[["user", "messages"]]
        d = d.sort_values(by=['messages'], ascending=False)
        return str(d.head().to_string(index=False))

    @staticmethod
    def get_date():
        return str(datetime.datetime.now()).split(" ")[0]

    def add_rep(self, user):
        try:
            id = self.get_usr(self.users, user)["_id"]
        except:
            id = None
        old, date = self.get_rep(user)
        if id != None:
          self.users.update_one({"_id":id}, {"$set":{"reps": old + 1}})
          self.users.update_one({"_id": id}, {"$set": {"last_rep": self.get_date()}})

    def get_rep(self, usr):
        try:
            u = self.get_usr(self.users, str(usr))
            return u["reps"], u["last_rep"]
        except Exception as e:
            print(e)
            return 0

    def rep_scoreboard(self):
        query = self.users.find({})
        usrs = []
        for doc in query:
            try:
                rep = int(doc["reps"])
                usrs.append([doc["user"], rep])
            except:
                pass
        usrs.sort(key=lambda x: x[1])
        usrs = usrs[-5:]

        df = pd.DataFrame(usrs, columns=["user", "reps"])
        d = df[["user", "reps"]]
        d = d.sort_values(by=['reps'], ascending=False)
        return str(d.head().to_string(index=False))
