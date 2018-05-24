import hashlib

from server.core.models.file import File
from server.errors.file_errors import *


class FileManager:

    def __init__(self):
        self.files_dict = dict()

    def add_file(self, file_id, path, size, checksum, chunk_size):
        if file_id not in self.files_dict.keys():
            raise IdAlreadyUsed

        for file in self.files_dict.values():
            if file.path == path:
                raise FileAlreadyExists

        if size == 0:
            raise ZeroSize

        self.files_dict[file_id] = File(file_id, path, size, checksum, chunk_size)

    def get_file_by_id(self, file_id):
        if file_id in self.files_dict.keys():
            return self.files_dict[file_id]

        return None

    @staticmethod
    def is_checksum_match(data, checksum):
        checksum_function = hashlib.md5()

        checksum_function.update(data)
        expected_checksum = checksum_function.hexdigest()

        if checksum == expected_checksum:
            return True

        return False

    def write_new_chunk(self, file_id, chunk_number, chunk_data, chunk_checksum):
        file = self.get_file_by_id(file_id)

        if file is None:
            raise FileNotFoundError

        if chunk_number != file.current_chunk + 1:
            raise InvalidChunkNumber

        if not file.is_checksum_match(chunk_data, chunk_checksum):
            raise ChecksumDoesNotMatch

        if not file.is_file_opened():
            file.open()

        file.write(chunk_data)
