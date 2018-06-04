import os
import hashlib
from typing import List
from datetime import datetime

from client.core.models.file import File
from client.errors.file_errors import *


class FileController:

    @staticmethod
    def from_path_list(path_list: List[str], chunk_size: int) -> List[File]:
        file_list = list()

        for path in path_list:
            try:
                file_list.append(File(path, chunk_size))
            except FileExistsError:
                pass  # TODO: Implement

        return file_list

    @staticmethod
    def set_name(file: File) -> None:
        file.name = file.path.split("/")[-1]

    @staticmethod
    def set_file_size(file: File) -> None:
        try:
            size = os.path.getsize(file.path)
        except os.error:
            return None

        file.size = size

    @staticmethod
    def set_file_checksum(file: File) -> None:
        if file.is_opened() and file.current_chunk == 0:
            checksum_function = hashlib.md5()

            for chunk in iter(lambda: file.file_object.read(file.chunk_size), b""):
                checksum_function.update(chunk)

            file.checksum = checksum_function.hexdigest()
            FileController.go_to_byte(file, 0)

    @staticmethod
    def set_chunk_checksum(file: File) -> None:
        if file.current_chunk_data is not None:
            checksum_function = hashlib.md5()
            checksum_function.update(file.current_chunk_data)

            file.current_chunk_checksum = checksum_function.hexdigest()

    @staticmethod
    def update_last_chunk_time(file: File) -> None:
        file.last_chunk_sent_time = datetime.now()

    @staticmethod
    def open(file: File) -> None:
        if file.is_opened():
            return None

        file.file_object = open(file.path, "rb")

        FileController.set_name(file)
        FileController.set_file_size(file)
        FileController.set_file_checksum(file)

    @staticmethod
    def close(file: File) -> None:
        if file.is_opened():
            file.file_object.close()

    @staticmethod
    def read(file: File) -> None:
        if not file.is_opened():
            FileController.open(file)

        if file.current_chunk == -1:
            raise EndOfFile

        file.current_chunk_data = file.file_object.read(file.chunk_size)

        if file.current_chunk_data == b"":
            file.current_chunk = -1
            raise EndOfFile

        current_chunk_size = len(file.current_chunk_data)

        FileController.set_chunk_checksum(file)
        file.total_bytes_sent += current_chunk_size
        file.current_chunk_size = current_chunk_size
        file.current_chunk += 1

    @staticmethod
    def go_to_byte(file: File, byte_number: int) -> None:
        if file.is_opened() and byte_number <= file.size:
            file.file_object.seek(byte_number)
