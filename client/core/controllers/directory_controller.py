import os

from client.core.models.directory import Directory
from client.core.models.file import File


class DirectoryController:

    def __init__(self, chunk_size: int):
        self.root_directories_list = list()
        self.chunk_size = chunk_size

    def add_directory(self, path: str) -> None:
        try:
            new_directory = Directory(path, self.chunk_size)
        except NotADirectoryError:
            return None

        if not self.is_directory_already_in_list(path):
            self.root_directories_list.append(new_directory)
            DirectoryController.set_content(new_directory)

    def is_directory_already_in_list(self, path: str) -> bool:
        for directory in self.root_directories_list:
            if directory.path == path:
                return True

        return False

    @staticmethod
    def set_name(directory: Directory) -> None:
        directory.name = directory.path.split("/")[-1]

    @staticmethod
    def set_content(directory) -> None:
        DirectoryController.set_name(directory)

        for element in os.listdir(directory.path):
            element_path = os.path.join(directory.path, element)

            if os.path.isdir(element_path):
                new_directory = Directory(element_path, directory.chunk_size, directory.level + 1)

                directory.sub_directories_list.append(new_directory)
                DirectoryController.set_content(new_directory)
            elif os.path.isfile(element_path):
                directory.files_list.append(File(element_path, directory.chunk_size))


if __name__ == '__main__':
    directory_controller = DirectoryController(15)
    directory_controller.add_directory("/home/user")
