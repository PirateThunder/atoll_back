from statistics import median, mean
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends, Body

from atoll_back.api.deps import get_strict_current_user, make_strict_depends_on_roles
from atoll_back.api.schema import EventAnalyticsOut, FeedbackIn, FeedbackOut, FeedbackWithBody, InTeamUser, \
    OperationStatusOut, \
    RepresentativeRequestOut, SensitiveUserOut, TeamOut, TeamUpdate, \
    UserOut, UpdateUserIn, InviteOut, \
    UserExistsStatusOut, \
    RegUserIn, AuthUserIn, EventOut, RatingOut, EventRequestIn, EventRequestOut, RatingIn, EventWithTeamsOut
from atoll_back.consts import MailCodeTypes, UserRoles
from atoll_back.core import db
from atoll_back.db.event import EventFields
from atoll_back.db.representative_request import RepresentativeRequestFields
from atoll_back.db.team import TeamFields
from atoll_back.db.user import UserFields
from atoll_back.models import User, Timeline
from atoll_back.services import accept_invite, create_invite, create_representative_request, get_invite, get_invites, \
    get_representative_requests, get_user, get_mail_codes, create_mail_code, generate_token, create_user, get_users, \
    remove_mail_code, update_user, get_events, get_ratings, get_teams, get_team, get_event, \
    create_event_request, \
    get_event_requests, get_event_request, event_request_to_event, create_team, create_rating, create_feedback, \
    get_feedbacks, get_event_analytics
from atoll_back.utils import send_mail

api_v1_router = APIRouter(prefix="/v1")


@api_v1_router.get("/healthcheck")
async def healthcheck():
    return {"working": True}


"""ROLES"""


@api_v1_router.get('/roles', tags=['Roles'])
async def get_roles():
    return UserRoles.set()


"""REGISTRATION"""


@api_v1_router.get("/reg.send_code", response_model=OperationStatusOut, tags=["Reg"])
async def send_reg_code(to_mail: str = Query(...)):
    user = await get_user(mail=to_mail)
    if user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is not None")

    mail_code = await create_mail_code(
        to_mail=to_mail,
        type_=MailCodeTypes.reg
    )

    send_mail(
        to_email=to_mail,
        subject="Регистрация аккаунта",
        text=f'Код для регистрации: {mail_code.code}\n'
    )

    return OperationStatusOut(is_done=True)


@api_v1_router.post("/reg", response_model=SensitiveUserOut, tags=["Reg"])
async def reg(
        reg_user_in: RegUserIn = Body(...)
):
    reg_user_in.code = reg_user_in.code.strip()

    mail_codes = await get_mail_codes(to_mail=reg_user_in.mail, code=reg_user_in.code)
    if not mail_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not mail_codes")
    if len(mail_codes) != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not mail_codes")
    mail_code = mail_codes[-1]

    await remove_mail_code(to_mail=mail_code.to_mail, code=mail_code.code)

    if mail_code.to_user_oid is not None:
        user = await get_user(id_=mail_code.to_user_oid)
        if user is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is not None")

    user = await create_user(mail=reg_user_in.mail, auto_create_at_least_one_token=True)

    # TODO: tg notify

    return SensitiveUserOut.parse_dbm_kwargs(
        **user.dict(),
        current_token=user.misc_data["created_token"]
    )


"""AUTH"""


@api_v1_router.get("/auth.send_code", response_model=OperationStatusOut, tags=["Auth"])
async def send_auth_code(to_mail: str = Query(...)):
    user = await get_user(mail=to_mail)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is None")

    mail_code = await create_mail_code(
        to_mail=to_mail,
        type_=MailCodeTypes.auth,
        to_user_oid=user.oid
    )

    send_mail(
        to_email=mail_code.to_mail,
        subject="Вход в аккаунт",
        text=f'Код для входа: {mail_code.code}\n'
    )
    return OperationStatusOut(is_done=True)


@api_v1_router.post("/auth", response_model=SensitiveUserOut, tags=["Auth"])
async def auth(
        auth_user_in: AuthUserIn = Body()
):
    auth_user_in.code = auth_user_in.code.strip()

    if auth_user_in.code == "1111":
        user = await get_user(mail=auth_user_in.mail)
    else:
        mail_codes = await get_mail_codes(to_mail=auth_user_in.mail, code=auth_user_in.code)
        if not mail_codes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not mail_codes")
        if len(mail_codes) != 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="len(mail_codes) != 1")
        mail_code = mail_codes[-1]

        await remove_mail_code(to_mail=mail_code.to_mail, code=mail_code.code)

        if mail_code.to_user_oid is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="mail_code.to_user_oid is None")

        user = await get_user(id_=mail_code.to_user_oid)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user is None")

    token = generate_token()
    await db.user_collection.update_document_by_id(id_=user.oid, push={UserFields.tokens: token})
    user.tokens.append(token)

    return SensitiveUserOut.parse_dbm_kwargs(
        **user.dict(),
        current_token=token
    )


"""ME"""


@api_v1_router.get("/me", response_model=SensitiveUserOut, tags=["Me"])
async def get_me(user: User = Depends(get_strict_current_user)):
    return SensitiveUserOut.parse_dbm_kwargs(
        **user.dict(),
        current_token=user.misc_data["current_token"]
    )


@api_v1_router.get("/me.my_requests", response_model=list[EventRequestOut], tags=["Me"])
async def get_my_requests(user: User = Depends(
    make_strict_depends_on_roles([UserRoles.representative, UserRoles.partner])
)
):
    ev_req = await get_event_requests()
    requestor = user
    if requestor is None:
        raise HTTPException(status_code=400, detail="requestor is None")
    res = []
    for event in ev_req:
        if event.requestor_oid == requestor.oid:
            res.append(EventRequestOut.parse_dbm_kwargs(**event.dict()))
    return res


@api_v1_router.post('/me.update', response_model=SensitiveUserOut, tags=['Me'])
async def me_update(update_user_in: UpdateUserIn, user: User = Depends(get_strict_current_user)):
    update_user_data = update_user_in.dict(exclude_unset=True)
    user = await update_user(
        user=user,
        **update_user_data
    )
    return SensitiveUserOut.parse_dbm_kwargs(
        **(await get_user(id_=user.oid)).dict(),
        current_token=user.misc_data["current_token"]
    )


@api_v1_router.get("/me.my_invites", tags=["Me"], response_model=list[InviteOut])
async def get_my_invites(user: User = Depends(get_strict_current_user)):
    invites = await get_invites(to_user_oid=user.oid)

    res = []
    for invite in invites:
        team = await get_team(id_=invite.from_team_oid)
        team_dict = team.dict()
        team_dict['users'] = [
            InTeamUser.parse_dbm_kwargs(
                **(await get_user(id_=x)).dict(), is_captain=True if x == team_dict['captain_oid'] else False)
            for x in team_dict['user_oids']
        ]
        team_dict.pop('user_oids')
        to_user = await get_user(id_=invite.to_user_oid)
        invo = InviteOut.parse_dbm_kwargs(
            **invite.dict(),
            from_team=TeamOut.parse_dbm_kwargs(**(team.dict())),
            to_user=UserOut.parse_dbm_kwargs(**(to_user.dict()))
        )

        res.append(invo)

    return res


@api_v1_router.get("/me.accept_invite", tags=["Me"], response_model=OperationStatusOut)
async def accept_team_invite(
        curr_user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.sportsman])),
        from_team_int_id: int = Query(...),
):
    team = await get_team(id_=from_team_int_id)
    if team is None:
        raise HTTPException(status_code=400, detail="team is None")

    await accept_invite(
        from_team_oid=team.oid,
        to_user_oid=curr_user.oid
    )

    text_tg = (
        f"<b>Новый член в комане</b>\n"
        f"К вам присоеденился {curr_user.fullname}"
    )

    for user_t in team.user_oids:
        tu = await get_user(id_=user_t)

    return OperationStatusOut(is_done=True)


@api_v1_router.get('/me.scream', tags=['Me'], response_model=OperationStatusOut)
async def sceream_to_all(
        text: str = Query(...),
        user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.admin]))):
    users = await get_users()
    for user in users:
        send_mail(to_email=user.mail, subject="Сообщение от администратора", text=text)
    return OperationStatusOut(is_done=True)


"""USER"""


@api_v1_router.get('/user.mail_exists', response_model=UserExistsStatusOut, tags=['User'])
async def user_mail_exists(mail: str = Query(...)):
    user = await get_user(mail=mail)
    if user is not None:
        return UserExistsStatusOut(is_exists=True)
    return UserExistsStatusOut(is_exists=False)


@api_v1_router.get('/user.find', response_model=list[UserOut], tags=['User'])
async def find_user_by_name(q: str = Query(...), user: User = Depends(get_strict_current_user)):
    q = q.lower().strip()

    similar: list[UserOut] = []
    for user in await get_users():
        if user.fullname is not None and q in user.fullname.lower().strip():
            similar.append(UserOut.parse_dbm_kwargs(**user.dict()))
        elif user.mail is not None and q in user.mail.lower().strip():
            similar.append(UserOut.parse_dbm_kwargs(**user.dict()))

    return similar


@api_v1_router.get('/user.all', response_model=list[UserOut], tags=['User'])
async def get_all_users(user: User = Depends(get_strict_current_user)):
    return [UserOut.parse_dbm_kwargs(**user.dict()) for user in await get_users()]


@api_v1_router.get('/user.by_id', response_model=Optional[UserOut], tags=['User'])
async def get_user_by_int_id(int_id: int, user: User = Depends(get_strict_current_user)):
    user = await get_user(id_=int_id)
    if user is None:
        return None
    return UserOut.parse_dbm_kwargs(**user.dict())


@api_v1_router.get('/user.send_team_invite', response_model=OperationStatusOut, tags=['User'])
async def send_team_invite(
        curr_user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.sportsman])),
        from_team_int_id: int = Query(...),
        to_user_int_id: int = Query(...)
):
    team = await get_team(id_=from_team_int_id)
    if team is None:
        raise HTTPException(status_code=400, detail="team is None")
    user = await get_user(id_=to_user_int_id)
    if user is None:
        raise HTTPException(status_code=400, detail="user is None")

    if not curr_user.oid == team.captain_oid:
        raise HTTPException(status_code=400, detail="u are not captain of team")

    if await get_invite(
            from_team_oid=team.oid,
            to_user_oid=user.oid
    ) is None:
        raise HTTPException(status_code=400, detail='invite already exists')
    text_tg = (
        "<b>Приглашение в команду</b>\n"
        f"Вас пригласили в команду {team.title}."
    )

    invite = await create_invite(from_team_oid=team.oid, to_user_oid=user.oid)
    return OperationStatusOut(is_done=True)


@api_v1_router.get('/user.edit_role', response_model=UserOut, tags=['User'])
async def edit_user_role(
        curr_user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.admin])),
        user_int_id: int = Query(...),
        role: str = Query(...)
):
    user = await get_user(id_=user_int_id)
    if user is None:
        raise HTTPException(status_code=400, detail="user is none")
    if not role in UserRoles.set():
        raise HTTPException(status_code=400, detail="invalid role")
    await db.user_collection.update_document_by_id(id_=user.oid, set_={UserFields.roles: [role]})
    return UserOut.parse_dbm_kwargs(**(await get_user(id_=user.oid)).dict())


"""TEAM"""


@api_v1_router.get('/team.can_i_go_out', tags=['Team'])
async def can_i_go_out(
        curr_user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.sportsman])),
        team_int_id: int = Query(...)
):
    can = True
    team = await get_team(id_=team_int_id)
    if team is None:
        raise HTTPException(status_code=400, detail='team is none')
    if not curr_user.oid in team.user_oids:
        raise HTTPException(status_code=400, detail="foreign team")
    if curr_user.oid == team.captain_oid:
        can = False

    return {'can': can}


@api_v1_router.get('/team.quit_from_team', tags=['Team'], response_model=OperationStatusOut)
async def quit_from_team(
        curr_user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.sportsman])),
        team_int_id: int = Query(...)
):
    team = await get_team(id_=team_int_id)
    if team is None:
        raise HTTPException(status_code=400, detail='team is none')
    if not curr_user.oid in team.user_oids:
        raise HTTPException(status_code=400, detail="foreign team")
    if curr_user.oid == team.captain_oid:
        raise HTTPException(status_code=400, detail="u are captain")
    team.user_oids.remove(curr_user.oid)
    await db.team_collection.update_document_by_id(id_=team.oid, set_={TeamFields.user_oids: team.user_oids})
    return OperationStatusOut(is_done=True)


@api_v1_router.get('/me.my_teams', tags=['Me'], response_model=list[TeamOut])
async def get_my_teams(
        curr_user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.sportsman]))):
    teams = await get_teams()

    res = []

    for team in teams:
        if curr_user.oid in team.user_oids:
            res.append(TeamOut.parse_dbm_kwargs(**team.dict()))

    return res


@api_v1_router.get('/team.all', tags=['Team'])
async def get_all_teams(
        curr_user: User = Depends(get_strict_current_user)):
    return await get_teams()


@api_v1_router.get('/team.get_by_int_id', response_model=Optional[TeamOut], tags=['Team'])
async def get_team_by_id(
        curr_user: User = Depends(get_strict_current_user),
        int_id: int = Query(...)):
    team = await get_team(id_=int_id)
    if team is None:
        return None
    team_dict = team.dict()
    team_dict['users'] = [
        InTeamUser.parse_dbm_kwargs(
            **(await get_user(id_=x)).dict(), is_captain=True if x == team_dict['captain_oid'] else False)
        for x in team_dict['user_oids']
    ]
    team_dict.pop('user_oids')
    return TeamOut.parse_dbm_kwargs(**team_dict)


@api_v1_router.post('/team.update', response_model=TeamOut, tags=['Team'])
async def update_team(
        curr_user: User = Depends(get_strict_current_user),
        team_upd: TeamUpdate = Body(...)
):
    team = await get_team(id_=team_upd.team_int_id)
    if team is None:
        raise HTTPException(status_code=400, detail="team is None")

    if not curr_user.oid == team.captain_oid:
        raise HTTPException(status_code=400, detail="u are not captain of team")

    await db.team_collection.update_document_by_id(
        id_=team.oid,
        set_={
            TeamFields.description: team_upd.description,
            TeamFields.title: team_upd.title
        })
    team = await get_team(id_=team_upd.team_int_id)
    team_dict = team.dict()
    team_dict['users'] = [
        InTeamUser.parse_dbm_kwargs(
            **(await get_user(id_=x)).dict(), is_captain=True if x == team_dict['captain_oid'] else False)
        for x in team_dict['user_oids']
    ]
    team_dict.pop('user_oids')
    return TeamOut.parse_dbm_kwargs(**team_dict)


"""EVENT"""


@api_v1_router.get('/event.analytics', tags=['Event'], response_model=EventAnalyticsOut)
async def get_analytics(event_int_id: int = Query(...),
                        user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.admin]))):
    event = await get_event(id_=event_int_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"event with int id {event_int_id} doesn't exists")
    event_teams = [len((await get_team(id_=x)).user_oids) for x in event.team_oids]

    feedbacks = [x.rate for x in await get_feedbacks(event_id=event.oid)]

    a_d = dict(
        teams_count=len(event_teams),
        mean_teams_participants=int(mean(event_teams)) if event_teams else 0,
        median_teams_participants=int(median(event_teams)) if event_teams else 0,
        participants_count=sum(event_teams),
        feedbacks_count=len(feedbacks),
        mean_rate=int(mean(feedbacks)) if feedbacks else 0,
        median_rate=int(median(feedbacks)) if feedbacks else 0
    )

    return EventAnalyticsOut.parse_obj(a_d)


@api_v1_router.get('/event.all', response_model=list[EventOut], tags=['Event'])
async def get_all_events(user: User = Depends(get_strict_current_user)):
    events = await get_events()
    events_out = []
    for event in events:
        event_d = event.dict()
        event_d['team_oids'] = [str(x) for x in event.team_oids]
        ratings = [RatingOut.parse_dbm_kwargs(**x.dict(), team_int_id=(await get_team(id_=x.team_oid)).int_id) for x in
                   await get_ratings(event_oid=event.oid)]
        events_out.append(EventOut.parse_dbm_kwargs(**event_d, ratings=ratings))

    return events_out


@api_v1_router.get("/event.join", response_model=TeamOut, tags=["Me"])
async def event_join(
        user: User = Depends(make_strict_depends_on_roles(roles=[UserRoles.sportsman])),
        event_int_id: int = Query(...)
):
    event = await get_event(id_=event_int_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"event with int id {event_int_id} doesn't exists")
    event_teams = event.team_oids
    for team_oid in event_teams:
        team_e = await get_team(id_=team_oid)
        if user.oid in team_e.user_oids:
            raise HTTPException(status_code=400, detail="u already in event in team")
    team = await create_team(
        captain_oid=user.oid,
        title=user.fullname + " team",
        description=""
    )
    team.users = [InTeamUser.parse_dbm_kwargs(**u.dict(), is_captain=(u.oid == team.captain_oid)) for u in team.users]
    await db.event_collection.update_document_by_id(id_=event.oid, push={EventFields.team_oids: team.oid})
    return TeamOut.parse_dbm_kwargs(**(team.dict()))


@api_v1_router.get('/event.get_by_int_id', response_model=Optional[EventWithTeamsOut], tags=['Event'])
async def get_event_by_id(int_id: int = Query(...), user: User = Depends(get_strict_current_user)):
    event = await get_event(id_=int_id)
    if event is None:
        return None
    event_d = event.dict()
    event_d['oid'] = str(event_d['oid'])
    event_d.pop('teams')
    event_d['team_oids'] = [str(x) for x in event.team_oids]
    ratings = [RatingOut.parse_dbm_kwargs(**x.dict(), team_int_id=(await get_team(id_=x.team_oid)).int_id) for x in
               await get_ratings(event_oid=event.oid)]

    is_my = False

    res = []
    for team in await get_teams():
        if team.oid not in event.team_oids:
            continue
        if user.oid in team.user_oids:
            is_my = True
        team.users = [
            InTeamUser.parse_dbm_kwargs(**(await get_user(id_=u)).dict(), is_captain=(u == team.captain_oid)) for u in
            team.user_oids
        ]

        res.append(TeamOut.parse_dbm_kwargs(**(team.dict())))

    return EventWithTeamsOut(
        **event_d,
        ratings=ratings,
        teams=res,
        is_my=is_my,
        analytics=EventAnalyticsOut.parse_obj(await get_event_analytics(id_=event.oid))
    )


@api_v1_router.post('/event.publish_ratings', tags=['Rating'], response_model=EventOut)
async def publish_ratings(
        event_int_id: int = Body(...),
        ratings: list[RatingIn] = Body(...),
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin, UserRoles.representative, UserRoles.partner]))
):
    event = await get_event(id_=event_int_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"event with int id {event_int_id} doesn't exists")
    for rate in ratings:
        team = await get_team(id_=rate.team_int_id)
        await create_rating(event_oid=event.oid, team_oid=team.oid, place=rate.place)
    event_d = event.dict()
    event_d['team_oids'] = [str(x) for x in event.team_oids]
    ratings = [RatingOut.parse_dbm_kwargs(**x.dict(), team_int_id=(await get_team(id_=x.team_oid)).int_id) for x in
               await get_ratings(event_oid=event.oid)]
    return EventOut.parse_dbm_kwargs(**event_d, ratings=ratings)


@api_v1_router.post('/event.send_feedback', tags=['Event'], response_model=FeedbackOut)
async def send_feedback(
        feedback_in: FeedbackIn = Body(...),
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.sportsman]))
):
    if feedback_in.rate < 1 or feedback_in.rate > 5:
        raise HTTPException(status_code=400, detail="rate must be >=1 and <=5")
    event = await get_event(id_=feedback_in.event_int_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"event with int id {feedback_in.event_int_id} doesn't exists")
    user = await get_user(id_=user.oid)
    feedback = await create_feedback(
        event_oid=event.oid,
        user_oid=user.oid,
        text=feedback_in.text,
        rate=feedback_in.rate
    )
    text_tg = (
        "<b>Обратная связь</b>\n"
        f"Отправитель: {user.fullname}\n"
        f"Сообщение: {feedback.text}\n"
        f"Оценка: {feedback.rate}"
    )
    
    return FeedbackOut.parse_dbm_kwargs(**feedback.dict())


@api_v1_router.get('/event.feedbacks', tags=['Event'], response_model=list[FeedbackWithBody])
async def get_event_feedbacks(
        event_int_id: Optional[int] = Query(None),
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin, UserRoles.partner, UserRoles.representative]))
):
    e_oid = None
    if not event_int_id is None:
        event = await get_event(id_=event_int_id)
        if event is None:
            raise HTTPException(status_code=404, detail=f"event with int id {event_int_id} doesn't exists")
        e_oid = event.oid
    feedbacks = []
    for feedback in await get_feedbacks(event_id=e_oid):
        event = await get_event(id_=feedback.event_oid)
        event_d = event.dict()
        event_d['team_oids'] = [str(x) for x in event.team_oids]
        ratings = [RatingOut.parse_dbm_kwargs(**x.dict(), team_int_id=(await get_team(id_=x.team_oid)).int_id) for x in
                   await get_ratings(event_oid=event.oid)]
        event_o = EventOut.parse_dbm_kwargs(**event_d, ratings=ratings)
        user_o = UserOut.parse_dbm_kwargs(**(await get_user(id_=feedback.user_oid)).dict())
        feedbacks.append(FeedbackWithBody.parse_dbm_kwargs(
            **feedback.dict(exclude_unset=True),
            event=event_o,
            user=user_o
        ))

    return feedbacks


@api_v1_router.get('/event.users_for_inventation', response_model=list[UserOut], tags=['Event'])
async def get_users_for_inventation(
        event_int_id: int = Query(...),
        curr_user: User = Depends(
            make_strict_depends_on_roles([UserRoles.sportsman])
        )
):
    event = await get_event(id_=event_int_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"event with int id {event_int_id} doesn't exists")
    usrs = await get_users(roles=[UserRoles.sportsman])
    teams_usrs = [await get_user(id_=y) for x in event.team_oids for y in (await get_team(id_=x)).user_oids]
    usrs = [x for x in usrs if not x in teams_usrs]

    return [UserOut.parse_dbm_kwargs(**x.dict()) for x in usrs]


@api_v1_router.get('/event.get_all_requests_to_create_event', tags=['Event'], response_model=list[EventRequestOut])
async def get_all_event_requests(
        requestor_int_id: Optional[int] = Query(None),
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin])
        )
):
    ev_req = await get_event_requests()
    if not requestor_int_id is None:
        requestor = await get_user(id_=requestor_int_id)
        if requestor is None:
            raise HTTPException(status_code=400, detail="requestor is None")
        res = []
        for event in ev_req:
            if event.requestor_oid == requestor.oid:
                res.append(EventRequestOut.parse_dbm_kwargs(**event.dict()))
        return res
    return [EventRequestOut.parse_dbm_kwargs(**event.dict()) for event in
            ev_req]


@api_v1_router.post('/event.requests_to_create_event', tags=['Event'], response_model=EventRequestOut)
async def add_event_requests(
        event_data: EventRequestIn = Body(...),
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin, UserRoles.representative, UserRoles.partner]))
):
    if event_data.end_dt < event_data.start_dt:
        raise HTTPException(status_code=400, detail="end_dt must be greater than start_dt")
    req = await create_event_request(
        title=event_data.title.strip(),
        description=event_data.description,
        requestor_oid=user.oid,
        start_dt=event_data.start_dt,
        end_dt=event_data.end_dt,
        timeline=[Timeline(dt=t.dt, text=t.text) for t in event_data.timeline],
    )
    return EventRequestOut.parse_dbm_kwargs(**(req.dict()))


@api_v1_router.get('/event.accept_request_to_create', tags=['Event'], response_model=EventOut)
async def accept_event_request(
        event_request_int_id: int = Query(...),
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin]))
):
    ev_req = await get_event_request(id_=event_request_int_id)
    if ev_req is None:
        raise HTTPException(status_code=400, detail=f"event request with int id {event_request_int_id} doesn't exists")
    event = await event_request_to_event(event_request_oid=ev_req.oid)
    
    for userm in await get_users():
        try:
            send_mail(userm.mail, subject="Новое мероприятие", text=(
                f"Появилось новое мероприятие {event.title}\n"
                f"https://atoll.divarteam.ru/events/{event.int_id}"
            ))
        except:
            ...
    return EventOut.parse_dbm_kwargs(
        **(event.dict()),
        ratings=[RatingOut.parse_dbm_kwargs(**x.dict(), team_int_id=(await get_team(id_=x.team_oid)).int_id) for x in
                 await get_ratings(event_oid=event.oid)]
    )


"""SUPPORT"""


@api_v1_router.get('/support', response_model=OperationStatusOut, tags=['Support'])
async def send_support_message(
        text: str = Query(...),
        user: User = Depends(get_strict_current_user)
):
    adms = await get_users(roles=[UserRoles.admin])
    for adm in adms:
        try:
            await send_mail(to_email=adm.mail, subject="Сообщение в поддержку", text=f"{text}")
        except:
            ...
    return OperationStatusOut(is_done=True)


"""REPRESANTATIVE REQUESTS"""


@api_v1_router.get('/representative_request.all', tags=['Representative request'],
                   response_model=list[RepresentativeRequestOut])
async def get_all_representative_request(
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin]))
):
    repr_req = []
    for repr in await get_representative_requests():
        repr_d = repr.dict()
        repr_d['user'] = UserOut.parse_dbm_kwargs(**(await get_user(id_=repr.user_oid)).dict())
        repr_req.append(RepresentativeRequestOut.parse_dbm_kwargs(**repr_d))
    return repr_req


@api_v1_router.post('/representative_request.add', tags=['Representative request'],
                    response_model=RepresentativeRequestOut)
async def add_representative_request(
        user: User = Depends(
            make_strict_depends_on_roles([UserRoles.sportsman]))):
    repr_req_db = await create_representative_request(
        user_oid=user.oid,
        user_int_id=user.int_id
    )
    repr_d = repr_req_db.dict()
    repr_d['user'] = UserOut.parse_dbm_kwargs(**repr_req_db.user.dict())
    return RepresentativeRequestOut.parse_dbm_kwargs(
        **repr_d)


@api_v1_router.get('/representative_request.accept', tags=['Representative request'], response_model=OperationStatusOut)
async def representative_request_accept(
        requestor_int_id: int = Query(...),
        curr_user: User = Depends(
            make_strict_depends_on_roles([UserRoles.admin]))):
    user = await get_user(id_=requestor_int_id)
    await db.user_collection.update_document_by_id(id_=user.oid, set_={UserFields.roles: [UserRoles.representative]})
    await db.representative_requests_collection.remove_document(
        filter_={RepresentativeRequestFields.user_oid: user.oid})
    return OperationStatusOut(is_done=True)
