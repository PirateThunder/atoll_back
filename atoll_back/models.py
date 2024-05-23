from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Interface, IPv4Address
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, Extra
from pydantic.fields import ModelField

from atoll_back.consts import RolesType
from atoll_back.db.base import BaseFields, Document
from atoll_back.db.event import EventFields
from atoll_back.db.event_request import EventRequestFields
from atoll_back.db.feedback import FeedbackFields
from atoll_back.db.invite import InviteFields
from atoll_back.db.mailcode import MailCodeFields
from atoll_back.db.rating import RatingFields
from atoll_back.db.representative_request import RepresentativeRequestFields
from atoll_back.db.team import TeamFields
from atoll_back.db.user import UserFields
from atoll_back.utils import roles_to_list


class BaseDBM(BaseModel):
    misc_data: dict[Any, Any] = Field(default={})

    # db fields
    oid: Optional[ObjectId] = Field(alias=BaseFields.oid)
    int_id: Optional[int] = Field(alias=BaseFields.int_id)
    created: Optional[datetime] = Field(alias=BaseFields.created)

    class Config:
        extra = Extra.ignore
        arbitrary_types_allowed = True
        allow_population_by_field_name = True

        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.timestamp()
        }

    def to_json(self, **kwargs) -> str:
        kwargs["indent"] = 2
        kwargs["ensure_ascii"] = False
        return self.json(**kwargs)

    def to_dict(self, only_db_fields: bool = True, **kwargs) -> dict:
        data = self.dict(**kwargs)
        if only_db_fields is True:
            for f in self.__fields__.values():
                f: ModelField
                if f.alias not in data:
                    continue
                if f.has_alias is False:
                    del data[f.alias]
                    continue
        return data

    @classmethod
    def parse_document(cls, doc: Document) -> BaseDBM:
        """get only fields that has alias and exists in doc"""
        doc_to_parse = {}
        for f in cls.__fields__.values():
            f: ModelField
            if f.has_alias is False:
                continue
            if f.alias not in doc:
                continue
            doc_to_parse[f.alias] = doc[f.alias]
        return cls.parse_obj(doc_to_parse)

    def document(self) -> Document:
        doc = self.dict(by_alias=True, exclude_none=False, exclude_unset=False, exclude_defaults=False)
        for f in self.__fields__.values():
            f: ModelField
            if f.alias not in doc:
                continue
            if f.has_alias is False:
                del doc[f.alias]
                continue
            if doc[f.alias] is None:
                continue
            if f.outer_type_ in [IPv4Interface, IPv4Address]:
                doc[f.alias] = str(doc[f.alias])
            elif f.outer_type_ in [list[IPv4Interface], list[IPv4Address]]:
                doc[f.alias] = [str(ip) for ip in doc[f.alias]]
        return doc


class User(BaseDBM):
    # db fields
    fullname: Optional[str] = Field(alias=UserFields.fullname)
    mail: Optional[str] = Field(alias=UserFields.mail)
    tokens: list[str] = Field(alias=UserFields.tokens, default=[])
    birth_dt: Optional[datetime] = Field(alias=UserFields.birth_dt)
    tg_username: Optional[str] = Field(alias=UserFields.tg_username)
    tg_id: Optional[str] = Field(alias=UserFields.tg_id)
    vk_id: Optional[str] = Field(alias=UserFields.vk_id)
    roles: list[str] = Field(alias=UserFields.roles, default=[])
    description: Optional[str] = Field(alias=UserFields.description)

    # direct linked models
    # ...

    # indirect linked models
    mail_codes: list[MailCode] = Field(default=[])

    def compare_roles(self, needed_roles: RolesType) -> bool:
        needed_roles = roles_to_list(needed_roles)
        return bool(set(needed_roles) & set(self.roles))

    @property
    def at_tg_username(self) -> str:
        if self.tg_username is not None:
            return f"@{self.tg_username}"
        return ""


class MailCode(BaseDBM):
    # db fields
    to_mail: str = Field(alias=MailCodeFields.to_mail)
    code: str = Field(alias=MailCodeFields.code)
    type: str = Field(alias=MailCodeFields.type)  # use MailCodeTypes
    to_user_oid: Optional[ObjectId] = Field(alias=MailCodeFields.to_user_oid)

    # direct linked models
    to_user: Optional[User] = Field(default=None)


class Team(BaseDBM):
    # db_fields
    captain_oid: ObjectId = Field(alias=TeamFields.captain_oid)
    title: str = Field(alias=TeamFields.title)
    description: str = Field(alias=TeamFields.description)
    user_oids: list[ObjectId] = Field(alias=TeamFields.user_oids)

    # direct linked models
    users: list[User] = Field(default=[])
    captain: Optional[User] = Field(default=None)


class Timeline(BaseModel):
    dt: datetime = Field(alias='dt')
    text: str = Field(alias='text')


class Rating(BaseDBM):
    # db fields
    event_oid: ObjectId = Field(alias=RatingFields.event_oid)
    team_oid: ObjectId = Field(alias=RatingFields.team_oid)
    place: int = Field(alias=RatingFields.place)

    # direct linked models
    event: Optional[Event] = Field(default=None)


class Event(BaseDBM):
    # db fields
    title: str = Field(alias=EventFields.title)
    description: str = Field(alias=EventFields.description)
    team_oids: Optional[list[ObjectId]] = Field(alias=EventFields.team_oids)
    start_dt: datetime = Field(alias=EventFields.start_dt)
    end_dt: datetime = Field(alias=EventFields.end_dt)
    timeline: list[Timeline] = Field(alias=EventFields.timeline)

    # direct linked models
    teams: list[Team] = Field(default=[])


class EventRequest(BaseDBM):
    # db fields
    title: str = Field(alias=EventRequestFields.title)
    description: str = Field(alias=EventRequestFields.description)
    requestor_oid: ObjectId = Field(alias=EventRequestFields.requestor_oid)
    start_dt: datetime = Field(alias=EventRequestFields.start_dt)
    end_dt: datetime = Field(alias=EventRequestFields.end_dt)
    timeline: list[Timeline] = Field(alias=EventRequestFields.timeline)

    # direct linked models
    requestor: Optional[User] = Field(default=None)


class Feedback(BaseDBM):
    # db fields
    event_oid: ObjectId = Field(alias=FeedbackFields.event_oid)
    user_oid: ObjectId = Field(alias=FeedbackFields.user_oid)
    text: str = Field(alias=FeedbackFields.text)
    rate: int = Field(alias=FeedbackFields.rate)

    # direct linked models
    user: Optional[User] = Field(default=None)
    event: Optional[Event] = Field(default=None)


class Invite(BaseDBM):
    # db fields
    from_team_oid: ObjectId = Field(alias=InviteFields.from_team_oid)
    to_user_oid: ObjectId = Field(alias=InviteFields.to_user_oid)

    # direct linked models
    user: Optional[User] = Field(default=None)
    team: Optional[Team] = Field(default=None)


class RepresentativeRequest(BaseDBM):
    # db fields
    user_oid: ObjectId = Field(alias=RepresentativeRequestFields.user_oid)
    user_int_id: int = Field(alias=RepresentativeRequestFields.user_int_id)

    # direct linked models
    user: Optional[User] = Field(default=None)
