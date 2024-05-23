from typing import Union

from atoll_back.helpers import SetForClass


class MailCodeTypes(SetForClass):
    reg = "reg"
    auth = "auth"


class UserRoles(SetForClass):
    sportsman = "sportsman"
    admin = "admin"
    representative = "representative"
    partner = "partner"
    dev = "dev"


RolesType = Union[set[str], list[str], str]


class Modes(SetForClass):
    prod = "prod"
    dev = "dev"


class TgBotCommands(SetForClass):
    start = "start"
    echo = "echo"
    events = "events"
    site = "site"
    my_events = "my_events"
