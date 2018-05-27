from typing import Tuple


class Protocol:

    @staticmethod
    def process_packet(data: bytearray) -> Tuple[int, bytearray]:
