import asyncio
import logging
from typing import Optional

from atoll_back.consts import RolesType
from atoll_back.core import vk_boty
from atoll_back.db.base import Id
from atoll_back.models import User
from atoll_back.services import get_user, get_users

log = logging.getLogger(__name__)


async def send_from_tg_bot(*, text: str, to_roles: Optional[RolesType] = None, to_user_ids: Optional[list[Id]] = None):
    if to_roles is None and to_user_ids is not None:
        users_to_send = [await get_user(id_=id_) for id_ in to_user_ids]
    elif to_user_ids is None:
        users_to_send: list[User] = await get_users(roles=to_roles)
    else:
        users_to_send: list[User] = await get_users()

    for user in users_to_send:
        if user.tg_id is None:
            continue
        try:
            await vk_boty.easy_vk.send_msg(
                user.tg_id,
                text
            )
        except Exception as e:
            log.exception(e)


async def __example():
    await send_from_tg_bot(text="ХУЙ")
    print(1)


if __name__ == '__main__':
    asyncio.run(__example())
