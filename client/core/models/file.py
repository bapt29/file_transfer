import os

from client.errors.file_errors import *


class File:

    def __init__(self, path: str, chunk_size: int):
        if not os.path.isfile(path):
            raise FileNotFound

        self.path = path
        self.name = None
        self.file = None
        self.size = 0
        self.checksum = None

        self.chunk_size = chunk_size * 1000  # Chunk in Ko
        self.current_chunk = 0
        self.current_chunk_data = None
        self.current_chunk_checksum = None

    def is_opened(self) -> bool:
        if self.file is None:
            return False

        return True


if __name__ == '__main__':
    test_file = File("test.py", 15)

    print(test_file.file)
