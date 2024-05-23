from atoll_back.db.base import BaseCollection, BaseFields


class RatingFields(BaseFields):
    event_oid = "event_oid"
    team_oid = "team_oid"
    place = "place"


class RatingCollection(BaseCollection):
    COLLECTION_NAME = "rating"
