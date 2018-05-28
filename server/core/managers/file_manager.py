import hashlib

from server.core.models.file import File
from server.errors.file_errors import *


class FileManager:

    @staticmethod
    def is_chunk_checksum_match(data: bytes, checksum: str):
        checksum_function = hashlib.md5()

        checksum_function.update(data)
        expected_checksum = checksum_function.hexdigest()

        if checksum == expected_checksum:
            return True

        return False

    @staticmethod
    def is_file_checksum_match(file: File):
        if file.is_file_opened():
            checksum_function = hashlib.md5()

            file.file.seek(0)

            for chunk in iter(lambda: file.file.read(file.chunk_size), b""):
                checksum_function.update(chunk)

            file.checksum = checksum_function.hexdigest()

    @staticmethod
    def write_new_chunk(file: File, chunk_number: int, chunk_size: int, chunk_data: bytes, chunk_checksum: str):
        if chunk_number != file.current_chunk + 1:
            raise InvalidChunkNumber

        if not FileManager.is_chunk_checksum_match(chunk_data, chunk_checksum):
            raise ChecksumDoesNotMatch

        if not file.is_file_opened():
            file.open()

        file.write(chunk_data)
        file.already_wrote_bytes += chunk_size
        file.current_chunk += 1
