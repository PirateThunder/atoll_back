import asyncio

from atoll_back.core import db
from atoll_back.log import setup_logging


async def drop_db():
    setup_logging()
    await db.drop_collections(only_using=False)


if __name__ == '__main__':
    asyncio.run(drop_db())
