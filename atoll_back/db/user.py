import pymongo

from atoll_back.db.base import BaseCollection, BaseFields


class UserFields(BaseFields):
    fullname = "fullname"
    mail = "mail"
    birth_dt = "birth_dt"
    tokens = "tokens"
    tg_id = "tg_id"
    vk_id = "vk_id"
    tg_username = "tg_username"
    roles = "roles"
    description = "description"


class UserCollection(BaseCollection):
    COLLECTION_NAME = "user"

    async def ensure_indexes(self):
        await super().ensure_indexes()
        self.pymongo_collection.create_index(
            [(UserFields.mail, pymongo.ASCENDING)],
            unique=True, sparse=True
        )
