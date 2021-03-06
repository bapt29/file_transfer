class File:

    def __init__(self, path, size, checksum, chunk_size):
        self.path = path
        self.file = None
        self.size = size
        self.checksum = checksum

        self.chunk_size = chunk_size * 1000  # Chunk in Ko
        self.current_chunk = 0

        self.open()

    def __del__(self):
        self.close()

    def is_file_opened(self):
        if self.file is None:
            return False

        return True

    def open(self, mode="wb"):
        if not self.is_file_opened():
            self.file = open(self.path, mode)

    def write(self, data):
        if not self.is_file_opened():
            self.open()

        try:
            self.file.write(data)
        except IOError as error:
            raise IOError(error)

    def read(self, size):
        if not self.is_file_opened():
            self.open("rb")

        return self.file.read(size)

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
