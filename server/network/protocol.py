from typing import Tuple
import struct


class Protocol:

    @staticmethod
    def confirmation_packet(response: bool) -> bytearray:
        data = bytearray()
        data.append(0x02)

        data.extend(bytearray(struct.pack("?", response)))

        return data

    @staticmethod
    def file_chunk_integrity_confirmation(response: bool) -> bytearray:
        data = bytearray()
        data.append(0x03)

        data.extend(bytearray(struct.pack("?", response)))

        return data

    @staticmethod
    def file_integrity_confirmation(response: bool) -> bytearray:
        data = bytearray()
        data.append(0x04)

        data.extend(bytearray(struct.pack("?", response)))

        return data
