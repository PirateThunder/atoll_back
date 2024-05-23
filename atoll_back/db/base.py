from __future__ import annotations

import logging
from datetime import datetime
from typing import Union, Any, Optional

import pymongo
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCursor, AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.cursor import Cursor
from pymongo.database import Database
from pymongo.results import InsertOneResult

from atoll_back.helpers import SetForClass

Document = dict[str, Any]
Filter = dict[str, Any]
Sort = list[tuple[str, int]]
Id = Union[int, str, ObjectId]


class SeqFields:
    oid = "_id"
    collection = "collection"
    key = "key"
    last_value = "last_value"


class SeqCollection:
    COLLECTION_NAME = "seq"

    def __init__(self, mongo_db: AsyncIOMotorDatabase):
        self.motor_collection = mongo_db.get_collection(self.COLLECTION_NAME)
        self.log = logging.getLogger(f'collection_{self.collection_name}')

    @property
    def collection_name(self) -> str:
        return self.motor_collection.name

    @classmethod
    def from_mongo_db(cls, mongo_db: AsyncIOMotorDatabase) -> SeqCollection:
        return cls(mongo_db)

    async def ensure_indexes(self):
        await self.motor_collection.create_index(
            [(SeqFields.collection, pymongo.ASCENDING)],
            unique=True, sparse=True
        )
        await self.motor_collection.create_index(
            [(SeqFields.key, pymongo.ASCENDING)],
            sparse=True
        )
        await self.motor_collection.create_index(
            [(SeqFields.collection, pymongo.ASCENDING), (SeqFields.key, pymongo.ASCENDING)],
            unique=True, sparse=True
        )
        self.log.info(f'base indexes were ensured on "{self.motor_collection.name}"')

    def __normalize_filter(self, filter_: Optional[Filter]):
        if filter_ is None:
            return {}
        return filter_

    async def insert_document(self, document: Document) -> Document:
        if BaseFields.oid in document and not isinstance(document[BaseFields.oid], ObjectId):
            del document[BaseFields.oid]
        inserted: InsertOneResult = await self.motor_collection.insert_one(document)
        document[BaseFields.oid] = inserted.inserted_id
        return document

    async def count_documents(self, filter_: Optional[Filter] = None) -> int:
        filter_ = self.__normalize_filter(filter_)
        return await self.motor_collection.count_documents(filter_)

    async def document_exists(self, filter_: Optional[Filter] = None) -> bool:
        return await self.count_documents(filter_) > 0

    async def collection_with_key_exists(self, *, collection_name: str, key: str) -> bool:
        return await self.document_exists(
            filter_={
                SeqFields.collection: collection_name,
                SeqFields.key: key
            }
        )

    async def update_document(self, filter_: Filter, set_: Document):
        filter_ = self.__normalize_filter(filter_)
        await self.motor_collection.update_one(filter_, {'$set': set_})

    def create_cursor(
            self,
            *,
            filter_: Filter = None,
            limit: int = None,
            skip: int = None,
            sort_: Sort = None
    ) -> AsyncIOMotorCursor:
        filter_ = self.__normalize_filter(filter_)
        cursor: Cursor = self.motor_collection.find(filter_)
        if limit is not None:
            cursor = cursor.limit(limit)
        if skip is not None:
            cursor = cursor.skip(skip)
        if sort_ is not None:
            cursor = cursor.sort(sort_)
        return cursor

    async def update_last_value(self, *, collection: str, key: str, last_value: Any):
        filter_ = {
            SeqFields.collection: collection,
            SeqFields.key: key
        }
        await self.update_document(
            filter_=self.__normalize_filter(filter_=filter_),
            set_={SeqFields.last_value: last_value}
        )


class BaseFields(SetForClass):
    oid = "_id"
    int_id = "int_id"
    created = "created"


class BaseCollection:
    COLLECTION_NAME = 'base'

    def __init__(self, *, motor_db: AsyncIOMotorDatabase, pymongo_db: Database):
        self.motor_db = motor_db
        self.pymongo_db = pymongo_db
        self.motor_collection = motor_db.get_collection(self.COLLECTION_NAME)
        self.pymongo_collection = pymongo_db.get_collection(self.COLLECTION_NAME)
        self._seq_collection = SeqCollection(motor_db)
        self.log = logging.getLogger(f'collection_{self.motor_collection.name}')

    @property
    def collection_name(self) -> str:
        return self.motor_collection.name

    @classmethod
    def from_mongo_db(cls, motor_db: AsyncIOMotorDatabase, pymongo_db: Database) -> BaseCollection:
        return cls(motor_db=motor_db, pymongo_db=pymongo_db)

    async def ensure_indexes(self):
        await self.motor_collection.create_index(
            [(BaseFields.int_id, pymongo.ASCENDING)],
            unique=True, sparse=True
        )
        await self._seq_collection.ensure_indexes()

        # create seq for int_id
        if not await self._seq_collection.collection_with_key_exists(
                collection_name=self.collection_name,
                key=BaseFields.int_id
        ):
            await self._seq_collection.insert_document({
                SeqFields.collection: self.collection_name,
                SeqFields.key: BaseFields.int_id,
                SeqFields.last_value: 0
            })

        self.log.info(f"base indexes were ensured on '{self.motor_collection.name}'")

    def __normalize_filter(self, filter_: Optional[Filter]):
        if filter_ is None:
            return {}
        return filter_

    def create_cursor(
            self,
            *,
            filter_: Filter = None,
            limit: int = None,
            skip: int = None,
            sort_: Sort = None
    ) -> AsyncIOMotorCursor:
        filter_ = self.__normalize_filter(filter_)
        cursor: Cursor = self.motor_collection.find(filter_)
        if limit is not None:
            cursor = cursor.limit(limit)
        if skip is not None:
            cursor = cursor.skip(skip)
        if sort_ is not None:
            cursor = cursor.sort(sort_)
        return cursor

    def create_id_filter(
            self,
            id_: Id,
            key_oid: str = BaseFields.oid,
            key_int_id: str = BaseFields.int_id
    ) -> Filter:
        filter_ = {}
        if isinstance(id_, int):
            filter_[key_int_id] = id_
        elif isinstance(id_, ObjectId):
            filter_[key_oid] = id_
        elif isinstance(id_, str):
            filter_[key_oid] = ObjectId(id_)
        else:
            raise ValueError('id_ is int or ObjectId')
        return filter_

    async def generate_int_id(self) -> int:
        seq_doc = await self._seq_collection.motor_collection.find_one_and_update(
            filter={SeqFields.collection: self.collection_name, SeqFields.key: BaseFields.int_id},
            update={"$inc": {SeqFields.last_value: 1}},
            return_document=ReturnDocument.AFTER
        )
        return seq_doc[SeqFields.last_value]

    async def insert_document(self, document: Document) -> Document:
        if BaseFields.int_id not in document:
            document[BaseFields.int_id] = await self.generate_int_id()
        else:
            cursor = self.create_cursor(
                filter_={},
                sort_=[(BaseFields.int_id, pymongo.DESCENDING)],
                limit=1
            )
            int_ids = [doc[BaseFields.int_id] async for doc in cursor]
            int_ids.append(document[BaseFields.int_id])
            int_ids.sort()
            max_int_id = int_ids[-1]
            await self._seq_collection.update_last_value(
                collection=self.collection_name,
                key=BaseFields.int_id,
                last_value=max_int_id
            )

        if BaseFields.created not in document:
            document[BaseFields.created] = datetime.utcnow()
        if BaseFields.oid in document and not isinstance(document[BaseFields.oid], ObjectId):
            del document[BaseFields.oid]
        inserted: InsertOneResult = await self.motor_collection.insert_one(document)
        document[BaseFields.oid] = inserted.inserted_id
        return document

    async def find_document(
            self, filter_: Optional[Filter] = None
    ) -> Optional[Document]:
        filter_ = self.__normalize_filter(filter_)
        document = await self.motor_collection.find_one(filter_)
        return document

    async def find_document_by_id(
            self, id_: Id
    ) -> Optional[Document]:
        filter_ = self.create_id_filter(id_)
        return await self.find_document(filter_)

    async def find_document_by_oid(
            self, oid: ObjectId
    ) -> Optional[Document]:
        return await self.find_document({BaseFields.oid: oid})

    async def find_document_by_int_id(
            self, int_id: int
    ) -> Optional[Document]:
        return await self.find_document({BaseFields.int_id: int_id})

    async def get_all_docs(self) -> list[Document]:
        cursor = self.create_cursor()
        return [doc async for doc in cursor]

    async def count_documents(self, filter_: Optional[Filter] = None) -> int:
        filter_ = self.__normalize_filter(filter_)
        return await self.motor_collection.count_documents(filter_)

    async def document_exists(self, filter_: Optional[Filter] = None) -> bool:
        return await self.count_documents(filter_) > 0

    async def id_exists(self, id_: Id) -> bool:
        return await self.document_exists(self.create_id_filter(id_))

    async def int_id_exists(self, int_id: Optional[int]) -> bool:
        return await self.document_exists({BaseFields.int_id: int_id})

    async def oid_exists(self, oid: Optional[ObjectId]) -> bool:
        return await self.document_exists({BaseFields.oid: oid})

    async def update_document(self, filter_: Filter, set_: Document):
        filter_ = self.__normalize_filter(filter_)
        await self.motor_collection.update_one(filter_, {'$set': set_})

    async def update_document_by_id(self, id_: Id, set_: Optional[Document] = None, push: Optional[Document] = None):
        if set_ is None and push is None:
            raise ValueError("set_ is None and push is None")

        filter_ = self.create_id_filter(id_=id_)
        update = {}
        if set_ is not None:
            update["$set"] = set_
        if push is not None:
            update["$push"] = push

        await self.motor_collection.update_one(filter_, update)

    async def update_document_by_oid(self, oid: ObjectId, set_: Document):
        await self.update_document({BaseFields.oid: oid}, set_)

    async def update_document_by_int_id(self, int_id: int, set_: Document):
        await self.update_document({BaseFields.int_id: int_id}, set_)

    async def remove_document(self, filter_: Filter):
        filter_ = self.__normalize_filter(filter_)
        await self.motor_collection.delete_one(filter_)

    async def remove_by_id(self, id_: Id):
        await self.remove_document(self.create_id_filter(id_))

    async def remove_by_oid(self, oid: ObjectId):
        await self.remove_document({BaseFields.oid: oid})

    async def remove_by_int_id(self, int_id: int):
        await self.remove_document({BaseFields.int_id: int_id})

    async def remove_documents(self, filter_: Optional[Filter] = None):
        filter_ = self.__normalize_filter(filter_)
        await self.motor_collection.delete_many(filter_)

    async def drop_collection(self):
        await self.motor_collection.drop()
        self.log.info(f'collection "{self.motor_collection.name}" was dropped')
