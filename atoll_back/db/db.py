import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConnectionFailure

from atoll_back.db.event import EventCollection
from atoll_back.db.event_request import EventRequestCollection
from atoll_back.db.feedback import FeedbackCollection
from atoll_back.db.invite import InviteCollection
from atoll_back.db.mailcode import MailCodeCollection
from atoll_back.db.rating import RatingCollection
from atoll_back.db.representative_request import RepresentativeRequestCollection
from atoll_back.db.team import TeamCollection
from atoll_back.db.user import UserCollection


class CannotConnectToDb(Exception):
    pass


class DB:
    def __init__(self, mongo_uri: str, mongo_db_name: str):
        self.log = logging.getLogger(__name__)

        # pymongo client
        self.pymongo_client = MongoClient(mongo_uri)
        self.pymongo_db = self.pymongo_client.get_database(mongo_db_name)

        # motor client
        self.motor_client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        self.motor_db: AsyncIOMotorDatabase = self.motor_client.get_database(mongo_db_name)

        # collections
        self.collections = []

        self.user_collection: UserCollection = UserCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.user_collection)

        self.mail_code_collection: MailCodeCollection = MailCodeCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.mail_code_collection)

        self.event_request_collection: EventRequestCollection = EventRequestCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.event_request_collection)

        self.event_collection: EventCollection = EventCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.event_collection)

        self.team_collection: TeamCollection = TeamCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.team_collection)

        self.invite_collection: InviteCollection = InviteCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.invite_collection)

        self.feedback_collection: FeedbackCollection = FeedbackCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.feedback_collection)

        self.rating = RatingCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.rating)

        self.representative_requests_collection: RepresentativeRequestCollection = RepresentativeRequestCollection.from_mongo_db(
            motor_db=self.motor_db,
            pymongo_db=self.pymongo_db
        )
        self.collections.append(self.representative_requests_collection)

    async def ensure_all_indexes(self):
        self.log.info('ensuring all indexes')
        for collection in self.collections:
            await collection.ensure_indexes()
        self.log.info('all indexes were ensured')

    async def drop_collections(self, only_using: bool = False):
        c = 0
        if only_using:
            self.log.info('removing only using collections')
            for using_collection in self.collections:
                await using_collection.drop_collection()
                c += 1
        else:
            self.log.info('removing all collections')
            for collection_name in await self.motor_db.list_collection_names():
                collection = self.motor_db.get_collection(collection_name)
                await collection.drop()
                c += 1
                self.log.info(f'collection "{collection_name}" was removed')
        self.log.info(f'collections({c}) were removed')

    async def check_conn(self):
        self.log.info('checking conn to db')
        try:
            await self.motor_client.server_info()
            self.pymongo_client.server_info()
        except ConnectionFailure as e:
            raise CannotConnectToDb(e)
        except OperationFailure as e:
            raise CannotConnectToDb(e)
        except Exception as e:
            raise CannotConnectToDb(e)
        self.log.info('db conn is good')

    async def is_conn_good(self) -> bool:
        try:
            await self.check_conn()
        except CannotConnectToDb:
            return False
        return True


async def __example():
    from atoll_back.core import db
    await db.team_collection.get_all_docs()


if __name__ == '__main__':
    asyncio.run(__example())
