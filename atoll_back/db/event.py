from atoll_back.db.base import BaseCollection, BaseFields


class EventFields(BaseFields):
    title = "title"
    description = "description"
    team_oids = "team_oids"
    start_dt = "start_dt"
    end_dt = "end_dt"
    ratings = "ratings"
    timeline = "timeline"


class EventCollection(BaseCollection):
    COLLECTION_NAME = "event"
