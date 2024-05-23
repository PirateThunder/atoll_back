import asyncio
from atoll_back.cache_dir import CacheDir
from atoll_back.db.db import DB
from atoll_back.settings import Settings
# from atoll_back.vk_bot.vkboty.vkboty import VkBoty

settings = Settings()
db = DB(mongo_uri=settings.mongo_uri, mongo_db_name=settings.mongo_db_name)
    
cache_dir = CacheDir(settings.cache_dirpath)

# vk_boty = VkBoty(settings.vk_bot_token, settings.vk_group_id)
