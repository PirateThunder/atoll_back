from atoll_back.db.base import BaseCollection, BaseFields


class RepresentativeRequestFields(BaseFields):
    user_oid = "user_oid"
    user_int_id = "user_int_id"


class RepresentativeRequestCollection(BaseCollection):
    COLLECTION_NAME = "representative_request"
