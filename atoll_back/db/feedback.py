from atoll_back.db.base import BaseCollection, BaseFields


class FeedbackFields(BaseFields):
    event_oid = "event_oid"
    user_oid = "user_oid"
    text = "text"
    rate = "rate"


class FeedbackCollection(BaseCollection):
    COLLECTION_NAME = "feedback"
