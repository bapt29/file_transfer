import os

from client.errors.file_errors import *


class File:

    def __init__(self, path: str, chunk_size: int):
        if not os.path.isfile(path):
            raise FileNotFound

        self.path = path
        self.name = None
        self.file_object = None
        self.size = 0
        self.checksum = None
        self.chunk_size = chunk_size * 10**3  # Chunk in Ko

        self.current_chunk = 0
        self.current_chunk_size = None
        self.current_chunk_data = None
        self.current_chunk_checksum = None

        self.total_bytes_sent = 0
        self.last_chunk_sent_time = None

    def is_opened(self) -> bool:
        if self.file_object is None:
            return False

        return True
