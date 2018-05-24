class ChecksumDoesNotMatch(Exception):
    pass


class InvalidChunkNumber(Exception):
    pass


class IdAlreadyUsed(Exception):
    pass


class FileAlreadyExists(Exception):
    pass


class ZeroSize(Exception):
    pass
