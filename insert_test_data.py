
import asyncio
from datetime import datetime, timedelta

from bson import ObjectId

from atoll_back.core import db
from atoll_back.log import setup_logging
from atoll_back.models import Rating, Timeline, Team
from atoll_back.services import create_user, create_event, get_users
from atoll_back.db.rating import RatingFields
from atoll_back.db.team import TeamFields


async def insert_test_data():
    l1 = []
    l2 = [2,5,3,2,2,5]
    print(set(l1) & set(l2))
    
    


if __name__ == '__main__':
    asyncio.run(insert_test_data())

