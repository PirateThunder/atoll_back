import os
import pathlib
from typing import Optional
from urllib.parse import quote

from pydantic import BaseSettings

from atoll_back.consts import Modes

BASE_DIRPATH: str = str(pathlib.Path(__file__).parent.parent)
ENV_FILEPATH: str = os.path.join(BASE_DIRPATH, '.env')


class Settings(BaseSettings):
    api_title: str = "ATOLL API"
    api_prefix: str = "/api"

    mongo_user: Optional[str] = None
    mongo_password: Optional[str] = None
    mongo_host: str
    mongo_port: int = 27017
    mongo_auth_db: Optional[str] = None
    mongo_db_name: str = "atoll"

    mailru_login: str
    mailru_password: str
    mailru_server: str = "smtp.mail.ru"
    mailru_port: int = 465

    tg_bot_token: str
    tg_bot_use_webhook: bool = False
    tg_webhook_host: Optional[str] = None
    tg_webhook_path: Optional[str] = None

    @property
    def tg_bot_webhook_url(self) -> Optional[str]:
        return (
            f"{self.tg_webhook_host}{self.tg_webhook_path}" if self.tg_webhook_host and self.tg_webhook_path else None
        )

    tg_bot_web_app_host: Optional[str] = None
    tg_bot_webapp_port: Optional[int] = 8083

    vk_bot_token: str
    vk_group_id: str = "220168186"

    cache_dirname: str = "cache"
    cache_dirpath: str = os.path.join(BASE_DIRPATH, cache_dirname)

    front_domain: str = "https://atoll.divarteam.ru"

    mode: str = Modes.dev

    emulate_mail_sending: bool = True

    @property
    def mongo_uri(self) -> str:
        mongo_uri = f'mongodb://'
        if self.mongo_user is not None:
            mongo_uri += self.mongo_user
            if self.mongo_password is not None:
                mongo_uri += ":" + quote(self.mongo_password) + "@"
        mongo_uri += self.mongo_host + ":" + str(self.mongo_port)
        if self.mongo_auth_db is not None:
            mongo_uri += f"/?authSource={self.mongo_auth_db}"
        return mongo_uri

    class Config:
        if os.path.exists(ENV_FILEPATH):
            env_file = ENV_FILEPATH

    log_filepath: str = os.path.join(BASE_DIRPATH, "story.log")


if __name__ == '__main__':
    print(Settings())
