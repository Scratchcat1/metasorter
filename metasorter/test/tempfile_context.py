from typing import Optional
import random
import string
import os


class TempFileContext:
    def __init__(self, dir: str, filename: Optional[str] = None, data: str = ""):
        self._dir = dir
        self._filename = filename or "".join(
            random.choice(string.ascii_letters) for x in range(32)
        )
        self._filepath = os.path.join(self._dir, self._filename)
        self._data = data

    def __enter__(self):
        with open(self._filepath, "w") as fh:
            fh.write(self._data)
        return self._filepath

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.remove(self._filepath)
