from typing import Tuple


class Protocol:

    @staticmethod
    def confirmation_packet(response: bool) -> bytearray:
        pass

    @staticmethod
    def file_chunk_integrity_confirmation(response: bool) -> bytearray:
        pass

    @staticmethod
    def file_integrity_confirmation(response: bool) -> bytearray:
        pass
