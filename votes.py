from pymongo import MongoClient
import pymongo
from database import DataBase


class Vote():
    def __init__(self):
        self.client = MongoClient("")
        self.database = self.client.heroku_2d7ckb75.votes

    def count_polls(self):
        """
        :return: amount of polls in database
        """
        query = self.database.find({})
        count = 0
        for _ in query:
            count += 1
        return count

    def load_current_poll(self):
        """
        :return: database document
        """
        id = self.count_polls()
        return self.load_poll(id)

    def __len__(self):
        poll = self.load_current_poll()
        return len(poll["options"])

    def load_poll(self, id):
        """
        :param id: int
        :return: database document
        """
        found = self.database.find_one({"id": id})
        return found

    def get_last_poll(self):
        print("run")
        id = self.count_polls()
        if id > 0:
            id = id -1
        poll = self.load_poll(id)
        return poll["desc"], poll["options"], poll["votes"]

    def get_current_poll(self):
        poll = self.load_current_poll()
        return poll["desc"], poll["options"], poll["votes"]

    def add_vote(self, option, user):
        """
        :param option: int
        :return: None
        """
        id = self.count_polls()
        poll = self.load_poll(id)
        poll_votes = poll["votes"]
        option = option - 1
        poll_votes[option] = poll_votes[option] + 1
        voted_users = poll["users"]

        if str(user) not in voted_users:
            voted_users.append(str(user))
            self.database.find_one_and_update({"id": id}, {"$set": {"users": voted_users,"votes": poll_votes}})
        else:
            return -1
    def remove_vote(self, option, user):
        """
        :param option: int
        :return: None
        """
        id = self.count_polls()
        poll = self.load_poll(id)
        poll_votes = poll["votes"]
        option = option - 1
        poll_votes[option] = poll_votes[option] - 1
        voted_users = poll["users"]

        if str(user) in voted_users:
            voted_users.remove(str(user))
            self.database.find_one_and_update({"id": id}, {"$set": {"users": voted_users,"votes": poll_votes}})
        else:
            return -1

    def add_poll(self, desc, options):
        """
        :param desc: string
        :param options: list
        """
        id = self.count_polls() + 1
        poll = {"id": id, "desc": desc, "options": options, "votes": [0 for x in range(len(options))],"users":[],"created":DataBase.get_date()}
        id = self.database.insert_one(poll).inserted_id
        return id

