import os
from typing import List

from client.core.models.directory import Directory
from client.core.models.file import File


class DirectoryController:

    @staticmethod
    def from_path_list(path_list: List[str], chunk_size: int) -> List[Directory]:
        directory_list = list()

        for path in path_list:
            try:
                new_directory = Directory(path)
            except NotADirectoryError:
                pass  # TODO: Implement
            else:
                directory_list.append(new_directory)
                DirectoryController.set_content(new_directory, chunk_size)

        return directory_list

    @staticmethod
    def set_name(directory: Directory) -> None:
        directory.name = directory.path.split("/")[-1]

    @staticmethod
    def set_content(directory: Directory, chunk_size: int) -> None:
        DirectoryController.set_name(directory)

        for element in os.listdir(directory.path):
            element_path = os.path.join(directory.path, element)

            if os.path.isdir(element_path):
                new_directory = Directory(element_path, directory.level + 1)

                directory.sub_directories_list.append(new_directory)
                DirectoryController.set_content(new_directory, chunk_size)
            elif os.path.isfile(element_path):
                directory.files_list.append(File(element_path, chunk_size))
