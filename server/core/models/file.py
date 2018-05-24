class File:

    def __init__(self, file_id, path, size, checksum, chunk_size):
        self.path = path
        self.id = file_id
        self.file = None
        self.size = size
        self.checksum = checksum

        self.chunk_size = chunk_size * 1000  # Chunk in Ko
        self.current_chunk = 0

        self.open()

    def is_file_opened(self):
        if self.file is None:
            return False

        return True

    def open(self):
        if self.is_file_opened():
            self.file = open(self.path, "wb")

    def write(self, data):
        if not self.is_file_opened():
            self.open()

        try:
            self.file.write(data)
        except IOError as error:
            raise IOError(error)
        else:
            self.current_chunk += 1
