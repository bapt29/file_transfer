import struct
import json
import binascii

from typing import Tuple

from client.errors.network_errors import *


class Protocol:

    @staticmethod
    def extract_packet_code(data: bytes) -> Tuple[int, bytes]:
        return data[0], data[1:]

    @staticmethod
    def unpack(data_format: str, data: bytes):
        if len(data_format) == 1:
            return struct.unpack(data_format, data[:struct.calcsize(data_format)])[0]
        elif len(data_format) > 1:
            return struct.unpack(data_format, data[:struct.calcsize(data_format)])

    @staticmethod
    def string_to_bytes(string: str) -> bytearray:
        string_bytes = string.encode("utf-8")
        string_bytes_length = len(string_bytes)

        return bytearray(struct.pack("I%ss" % string_bytes_length, string_bytes_length, string_bytes))

    @staticmethod
    def bytes_to_unsigned_int(data: bytes) -> int:
        return Protocol.unpack("I", data)

    @staticmethod
    def bytes_to_bool(data) -> bool:
        return Protocol.unpack("?", data)

    @staticmethod
    def send_create_new_directory(name: str) -> bytearray:
        code = 0x01
        data = bytearray()

        data.append(code)
        data.extend(Protocol.string_to_bytes(name))

        return data

    @staticmethod
    def send_create_new_file(name: str, size: int, checksum: str) -> bytearray:
        code = 0x02
        data = bytearray()
        data.append(code)

        file = {"name": name, "size": size, "checksum": checksum}

        file_data = Protocol.string_to_bytes(json.dumps(file))
        data.extend(file_data)

        return data

    @staticmethod
    def send_file_chunk(file_name: str,
                        chunk_number: int,
                        chunk_data: bytes,
                        chunk_checksum: str) -> bytearray:

        code = 0x03
        data = bytearray()
        data.append(code)

        header = {"file_name": file_name,
                  "chunk_number": chunk_number,
                  "chunk_size": len(chunk_data),
                  "chunk_data": binascii.hexlify(chunk_data).decode(),
                  "chunk_checksum": chunk_checksum}

        header_bytes = Protocol.string_to_bytes(json.dumps(header))
        data.extend(header_bytes)

        return data

    @staticmethod
    def send_end_of_file(name: str) -> bytearray:
        code = 0x04
        data = bytearray()

        data.append(code)
        data.extend(Protocol.string_to_bytes(name))

        return data

    @staticmethod
    def send_end_of_directory(name: str):
        code = 0x05
        data = bytearray()

        data.append(code)
        data.extend(Protocol.string_to_bytes(name))

        return data

    @staticmethod
    def send_file_transfer_abort(name: str) -> bytearray:
        code = 0x06
        data = bytearray()

        data.append(code)
        data.extend(Protocol.string_to_bytes(name))

        return data

    @staticmethod
    def receive_chunk_size(data: bytes) -> int:
        code, packet_data = Protocol.extract_packet_code(data)

        if code != 0x01:
            raise InvalidPacket(code)

        return Protocol.bytes_to_unsigned_int(packet_data)

    @staticmethod
    def receive_confirmation_packet(data: bytes) -> bool:
        code, packet_data = Protocol.extract_packet_code(data)

        if code != 0x02:
            raise InvalidPacket(code)

        return Protocol.bytes_to_bool(packet_data)

    @staticmethod
    def receive_file_chunk_integrity_confirmation(data: bytes) -> bool:
        code, packet_data = Protocol.extract_packet_code(data)

        if code != 0x03:
            raise InvalidPacket(code)

        return Protocol.bytes_to_bool(data)

    @staticmethod
    def receive_file_integrity_confirmation(data: bytes) -> bool:
        code, packet_data = Protocol.extract_packet_code(data)

        if code != 0x04:
            raise InvalidPacket(code)

        return Protocol.bytes_to_bool(data)
