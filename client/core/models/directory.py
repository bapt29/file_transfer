import os


class Directory:

    def __init__(self, path: str, level=0):
        if not os.path.isdir(path):
            raise NotADirectoryError

        self.path = path
        self.name = None
        self.level = level

        self.sub_directories_list = list()
        self.files_list = list()
