import os
import uuid
from typing import Optional


class CacheDir:
    def __init__(self, cache_dir: str):
        self.__cache_dir = cache_dir
        self.create_cache_dir()

    def create_cache_dir(self):
        if not os.path.exists(self.__cache_dir):
            os.mkdir(self.__cache_dir)

    def generate_filepath(
            self,
            create_if_not_exists: bool = False,
            file_extension: Optional[str] = None,
            text: Optional[str] = None
    ) -> str:
        if text is None:
            text = ""

        self.create_cache_dir()

        # generate filename
        filename = str(uuid.uuid4())
        if file_extension is not None:
            filename += f".{file_extension}"
        while filename in os.listdir(self.__cache_dir):
            filename = str(uuid.uuid4())
            if file_extension is not None:
                filename += f".{file_extension}"
        filepath = os.path.join(self.__cache_dir, filename)

        # create if not
        if create_if_not_exists is True and not os.path.exists(filepath):
            with open(filepath, mode='w') as f:
                f.write(text)

        return filepath

    def remove(self, filepath: str):
        self.create_cache_dir()

        filepath = os.path.join(self.__cache_dir, filepath)
        if os.path.exists(filepath):
            os.remove(filepath)


def test_cache_dir():
    from atoll_back.core import settings
    cache_dir = CacheDir(cache_dir=settings.cache_dirpath)
    were = set()
    for _ in range(1000):
        filepath = cache_dir.generate_filepath(file_extension="jpg", create_if_not_exists=True)
        assert filepath not in were
        were.add(filepath)


if __name__ == '__main__':
    test_cache_dir()
