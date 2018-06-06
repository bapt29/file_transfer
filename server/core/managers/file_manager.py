import hashlib

from server.core.models.file import File
from server.errors.file_errors import *


class FileManager:

    @staticmethod
    def is_chunk_checksum_match(data: bytes, checksum: str) -> bool:
        checksum_function = hashlib.md5()

        checksum_function.update(data)
        expected_checksum = checksum_function.hexdigest()

        return checksum == expected_checksum

    @staticmethod
    def is_file_checksum_match(file: File) -> bool:
        if file.is_file_opened():
            file.close()

        checksum_function = hashlib.md5()

        file.open("rb")

        for chunk in iter(lambda: file.read(file.chunk_size), b""):
            checksum_function.update(chunk)

        return file.checksum == checksum_function.hexdigest()

    @staticmethod
    def write_new_chunk(file: File, chunk_number: int, chunk_data: bytes, chunk_checksum: str):
        if chunk_number != file.current_chunk + 1:
            raise InvalidChunkNumber

        if not FileManager.is_chunk_checksum_match(chunk_data, chunk_checksum):
            raise ChecksumDoesNotMatch

        if not file.is_file_opened():
            file.open()

        file.write(chunk_data)
        file.current_chunk += 1
