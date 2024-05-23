from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from bson import ObjectId
from pydantic import BaseModel, Extra


class BaseSchema(BaseModel):
    class Config:
        extra = Extra.ignore
        arbitrary_types_allowed = True
        allow_population_by_field_name = True


class BaseSchemaOut(BaseSchema):
    misc: dict[str, Any] = {}


class BaseOutDBMSchema(BaseSchemaOut):
    oid: str
    int_id: int
    created: datetime

    @classmethod
    def parse_dbm_kwargs(
            cls,
            **kwargs
    ):
        res = {}
        for k, v in kwargs.items():
            if isinstance(v, ObjectId):
                v = str(v)
            res[k] = v
        return cls(**res)


class BaseSchemaIn(BaseSchema):
    pass


class RatingOut(BaseOutDBMSchema):
    event_oid: str
    place: int
    team_int_id: int


class RatingIn(BaseSchemaIn):
    place: int
    team_int_id: int


class TimelineOut(BaseModel):
    dt: datetime
    text: str


class EventOut(BaseOutDBMSchema):
    title: str
    description: str
    team_oids: Optional[list[str]]
    start_dt: datetime
    end_dt: datetime
    timeline: list[TimelineOut]
    ratings: list[RatingOut]


class EventWithTeamsOut(EventOut):
    teams: list[TeamOut]
    is_my: bool
    analytics: EventAnalyticsOut


class InviteOut(BaseOutDBMSchema):
    from_team_oid: str
    to_user_oid: str
    from_team: TeamOut
    to_user: UserOut


class EventRequestOut(BaseOutDBMSchema):
    title: str
    description: str
    requestor_oid: str
    start_dt: datetime
    end_dt: datetime
    timeline: list[TimelineOut]


class EventAnalyticsOut(BaseModel):
    teams_count: int
    mean_teams_participants: int
    median_teams_participants: int
    participants_count: int
    feedbacks_count: int
    mean_rate: int
    median_rate: int


class EventRequestIn(BaseSchemaIn):
    title: str
    description: str
    start_dt: datetime
    end_dt: datetime
    timeline: list[TimelineOut]


class FeedbackOut(BaseOutDBMSchema):
    event_oid: str
    user_oid: str
    text: str
    rate: int


class FeedbackWithBody(FeedbackOut):
    event: EventOut
    user: UserOut


class FeedbackIn(BaseSchemaIn):
    event_int_id: int
    text: str
    rate: int


class UserOut(BaseOutDBMSchema):
    fullname: Optional[str] = None
    mail: str
    birth_dt: Optional[datetime] = None
    tg_username: Optional[str] = None
    tg_id: Optional[str] = None
    vk_id: Optional[str] = None
    roles: list[str] = []
    description: Optional[str] = None


class InTeamUser(UserOut):
    is_captain: bool


class TeamOut(BaseOutDBMSchema):
    captain_oid: str
    title: str
    description: str
    users: list[InTeamUser]


class TeamUpdate(BaseSchemaIn):
    team_int_id: int
    title: str
    description: str


class SensitiveUserOut(UserOut):
    tokens: list[str]
    current_token: str


class OperationStatusOut(BaseSchemaOut):
    is_done: bool


class ExistsStatusOut(BaseSchemaOut):
    is_exists: bool


class UpdateUserIn(BaseSchemaIn):
    fullname: Optional[str] = None
    birth_dt: Optional[datetime] = None
    tg_username: Optional[str] = None
    vk_id: Optional[str] = None
    description: Optional[str] = None


class UserExistsStatusOut(BaseSchemaOut):
    is_exists: bool


class RegUserIn(BaseSchemaIn):
    mail: str
    code: str


class AuthUserIn(BaseSchemaIn):
    mail: str
    code: str


class RepresentativeRequestOut(BaseOutDBMSchema):
    user_oid: str
    user_int_id: int

    user: UserOut


RepresentativeRequestOut.update_forward_refs()
EventWithTeamsOut.update_forward_refs()
InviteOut.update_forward_refs()
FeedbackWithBody.update_forward_refs()
