import pymongo

from atoll_back.db.base import BaseCollection, BaseFields


class MailCodeFields(BaseFields):
    to_mail = "to_mail"
    code = "code"
    type = "type"
    to_user_oid = "to_user_oid"


class MailCodeCollection(BaseCollection):
    COLLECTION_NAME = "mail_code"

    async def ensure_indexes(self):
        await super().ensure_indexes()
        self.motor_collection.create_index(
            [(MailCodeFields.code, pymongo.ASCENDING)],
            unique=True, sparse=True
        )
        self.motor_collection.create_index(
            [
                (MailCodeFields.code, pymongo.ASCENDING),
                (MailCodeFields.to_mail, pymongo.ASCENDING)
            ],
            unique=True, sparse=True
        )
        self.motor_collection.create_index(
            [
                (MailCodeFields.code, pymongo.ASCENDING),
                (MailCodeFields.oid, pymongo.ASCENDING)
            ],
            unique=True, sparse=True
        )
