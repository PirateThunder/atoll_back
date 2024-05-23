

import asyncio

from atoll_back.core import db
from atoll_back.log import setup_logging


async def init_db():
    setup_logging()
    await db.ensure_all_indexes()


if __name__ == '__main__':
    asyncio.run(init_db())
