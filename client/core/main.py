from client.core.controllers.directory_controller import DirectoryController
from client.core.controllers.file_controller import FileController

from client.core.models.directory import Directory
from client.core.models.file import File

from client.errors.directory_errors import *
from client.errors.file_errors import *


class Main:

    def __init__(self, directory_controller, file_controller):
        self.directory_controller = directory_controller
        self.file_controller = file_controller

    def send_single_files(self):
        for file in self.file_controller.

    def send_directories(self):
        for main_directory in self.directory_controller.root_directories_list:
            self.send_directory(main_directory)

    def send_file(self, file: File):


    def send_directory(self, current_directory: Directory):
        for file in current_directory.files_list:
            self.send_file(file)

        for sub_directory in current_directory.sub_directories_list:
            self.send_directory(sub_directory)
