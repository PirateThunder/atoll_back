import os
import zipfile
from typing import Any


class NotSet:
    pass


def is_set(v: Any) -> bool:
    return not (v is NotSet or isinstance(v, NotSet))


class SetForClass:
    @classmethod
    def set(cls) -> set[str]:
        keys = list(cls.__dict__.keys())
        res = {
            cls.__dict__[k]
            for k in keys
            if isinstance(k, str) and not k.startswith('__') and not k.endswith('__') and k != 'set'
        }
        return res


def zipdir(dirpath: str, zip_filepath: str):
    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(dirpath):
            for file in files:
                zip_file.write(os.path.join(root, file),
                               os.path.relpath(os.path.join(root, file),
                                               os.path.join(dirpath, '..')))
