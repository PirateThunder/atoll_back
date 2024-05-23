from atoll_back.log import setup_logging
from atoll_back.tg_bot.main import main


def start_tg_bot():
    setup_logging()
    main()


if __name__ == '__main__':
    start_tg_bot()
