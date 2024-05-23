import asyncio
from datetime import datetime, timedelta

from atoll_back.consts import UserRoles
from atoll_back.core import db
from atoll_back.log import setup_logging
from atoll_back.models import Event, Team, Timeline, User


async def insert_test_data():
    setup_logging()
    await db.drop_collections()
    await db.ensure_all_indexes()

    await db.user_collection.insert_document({
        'fullname': "Arsen",
        'mail': "sabarsenrash@gmail.com",
        'tokens': ['3333'],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "arpakit",
        'tg_id': "269870432",
        'vk_id': "",
        'roles': [UserRoles.admin],
        'description': "Я Арсен"
    })

    await db.user_collection.insert_document({
        'fullname': "Rustam",
        'mail': "recrea.tor@yandex.ru",
        'tokens': ['4444'],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "rcr_tg",
        'tg_id': "373740493",
        'vk_id': "",
        'roles': [UserRoles.representative],
        'description': "Я Рустам"
    })
    await db.user_collection.insert_document({
        'fullname': "Ilya",
        'mail': "ilyakhakimov03@gmail.com",
        'tokens': ['2222'],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "pirat2003",
        'tg_id': "1525214974",
        'vk_id': "",
        'roles': [UserRoles.partner],
        'description': "Я Илья"
    })
    await db.user_collection.insert_document({
        'fullname': "Denchik",
        'mail': "dbarov3@gmail.com",
        'tokens': ["1111"],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "brightos",
        'tg_id': "426220634",
        'vk_id': "",
        'roles': [UserRoles.sportsman],
        'description': "Я Денис"
    })
    await db.user_collection.insert_document({
        'fullname': "Ivanya",
        'mail': "ermolovivan2018@gmail.com",
        'tokens': ['5555'],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "ivan_20190721",
        'tg_id': "457643251",
        'vk_id': "",
        'roles': [UserRoles.sportsman],
        'description': "Я Иван"
    })

    for i in range(5):
        tu1: User = User.parse_document(await db.user_collection.insert_document({
            'fullname': f"Спортсмен 1 {i}",
            'mail': f"testmailjk1_{i}@test.ru",
            'tokens': [],
            'birth_dt': datetime.utcnow().isoformat(),
            'tg_username': "",
            'tg_id': "",
            'vk_id': "",
            'roles': [UserRoles.sportsman],
            'description': ""
        }))
        tu2: User = User.parse_document(await db.user_collection.insert_document({
            'fullname': f"Спортсмен 2 {i}",
            'mail': f"teskl;tmail2_{i}@test.ru",
            'tokens': [],
            'birth_dt': datetime.utcnow().isoformat(),
            'tg_username': "",
            'tg_id': "",
            'vk_id': "",
            'roles': [UserRoles.sportsman],
            'description': ""
        }))
        tu3: User = User.parse_document(await db.user_collection.insert_document({
            'fullname': f"Спортсмен 3 {i}",
            'mail': f"testhjkmail3_{i}@test.ru",
            'tokens': [],
            'birth_dt': datetime.utcnow().isoformat(),
            'tg_username': "",
            'tg_id': "",
            'vk_id': "",
            'roles': [UserRoles.sportsman],
            'description': ""
        }))
        team: Team = Team.parse_document(await db.team_collection.insert_document({
            'captain_oid': tu1.oid,
            'title': f'test team {i}',
            'description': f"team with {tu1.fullname} {tu2.fullname} {tu3.fullname}",
            'user_oids': [tu1.oid, tu2.oid, tu3.oid, ]
        }))
        Event.parse_document(await db.event_collection.insert_document({
            'title': f'Event {i}',
            'description': f'Description event {i}',
            'team_oids': [team.oid],
            'start_dt': datetime.now() - timedelta(days=1),
            'end_dt': datetime.now() + timedelta(days=30),
            'timeline': [
                Timeline(dt=datetime.now(), text="завтрак").dict(),
                Timeline(dt=datetime.now() + timedelta(days=1), text="Обед").dict(),
                Timeline(dt=datetime.now() + timedelta(days=2), text="Ужин").dict()
            ],
        }))

    await db.user_collection.insert_document({
        'fullname': "Тестовый представитель",
        'mail': "testmtyuiail1@test.ru",
        'tokens': [],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "no exists",
        'tg_id': "",
        'vk_id': "",
        'roles': [UserRoles.representative],
        'description': ""
    })
    await db.user_collection.insert_document({
        'fullname': "Тестовый Партнер",
        'mail': "testmail2@test.ru",
        'tokens': [],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "",
        'tg_id': "",
        'vk_id': "",
        'roles': [UserRoles.partner],
        'description': ""
    })

    await db.user_collection.insert_document({
        'fullname': "Dev1",
        'mail': "testmail4@test.ru",
        'tokens': [],
        'birth_dt': datetime.utcnow().isoformat(),
        'tg_username': "",
        'tg_id': "",
        'vk_id': "",
        'roles': [UserRoles.dev],
        'description': ""
    })

    await db.event_collection.insert_document({
        'title': 'Всероссийский хакатон фсп 2023 Воронеж',
        'description': 'Всероссийский хакатон фсп для студентов',
        'team_oids': [],
        'start_dt': datetime.now(),
        'end_dt': datetime.now() + timedelta(days=2),
        'timeline': [
            Timeline(dt=datetime.now(), text="старт").dict(),
            Timeline(dt=datetime.now() + timedelta(days=1), text="чекпоинт").dict(),
            Timeline(dt=datetime.now() + timedelta(days=2), text="конец").dict()],
    })
    await db.event_collection.insert_document({
        'title': 'Тестовый хакатон 2023',
        'description': 'Тестовый хакатон для теста',
        'team_oids': [],
        'start_dt': datetime.now(),
        'end_dt': datetime.now() + timedelta(days=3),
        'timeline': [
            Timeline(dt=datetime.now(), text="старт").dict(),
            Timeline(dt=datetime.now() + timedelta(days=1), text="чекпоинт").dict(),
            Timeline(dt=datetime.now() + timedelta(days=2), text="чекпоинт").dict(),
            Timeline(dt=datetime.now() + timedelta(days=3), text="конец").dict(), ],
    })


if __name__ == '__main__':
    asyncio.run(insert_test_data())
