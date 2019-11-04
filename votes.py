from motor.motor_asyncio import AsyncIOMotorClient
import pymongo
from database import DataBase


class Vote():
    def __init__(self):
        self.client = AsyncIOMotorClient("")
        self.database = self.client.heroku_2d7ckb75.votes

    async def count_polls(self):
        """
        :return: amount of polls in database
        """
        query = self.database.find({})
        data = await query.to_list(length=1000)
        count = 0
        for _ in data:
            count += 1
        return count

    async def load_current_poll(self):
        """
        :return: database document
        """
        await id = self.count_polls()
        return await self.load_poll(id)

    async def get_len(self):
        poll = self.load_current_poll()
        return len(poll["options"])

    async def load_poll(self, id):
        """
        :param id: int
        :return: database document
        """
        found = await self.database.find_one({"id": id})
        return found

    async def get_last_poll(self):
        print("run")
        id = await self.count_polls()
        if id > 0:
            id = id -1
        poll = await self.load_poll(id)
        return poll["desc"], poll["options"], poll["votes"]

    async def get_current_poll(self):
        poll = await self.load_current_poll()
        return poll["desc"], poll["options"], poll["votes"]

    async def add_vote(self, option, user):
        """
        :param option: int
        :return: None
        """
        id = await self.count_polls()
        poll = await self.load_poll(id)
        poll_votes = poll["votes"]
        option = option - 1
        poll_votes[option] = poll_votes[option] + 1
        voted_users = poll["users"]

        if user.id not in voted_users:
            voted_users.append(user.id)
            await self.database.find_one_and_update({"id": id}, {"$set": {"users": voted_users,"votes": poll_votes}})
        else:
            return -1
    async def remove_vote(self, option, user):
        """
        :param option: int
        :return: None
        """
        id = await self.count_polls()
        poll = await self.load_poll(id)
        poll_votes = poll["votes"]
        option = option - 1
        poll_votes[option] = poll_votes[option] - 1
        voted_users = poll["users"]

        if user.id in voted_users:
            voted_users.remove(user.id)
            await self.database.find_one_and_update({"id": id}, {"$set": {"users": voted_users,"votes": poll_votes}})
        else:
            return -1

    async def add_poll(self, desc, options):
        """
        :param desc: string
        :param options: list
        """
        id = await self.count_polls() + 1
        poll = {"id": id, "desc": desc, "options": options, "votes": [0 for x in range(len(options))],"users":[],"created":DataBase.get_date()}
        id = await self.database.insert_one(poll).inserted_id
        return id

