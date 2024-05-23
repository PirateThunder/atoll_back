from atoll_back.db.base import BaseCollection, BaseFields


class InviteFields(BaseFields):
    from_team_oid = "from_team_oid"
    to_user_oid = "to_user_oid"


class InviteCollection(BaseCollection):
    COLLECTION_NAME = "invite"
