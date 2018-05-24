import struct
import json
import binascii


class Protocol:

    @staticmethod
    def string_to_bytes(string: str) -> bytearray:
        string_bytes = string.encode("utf-8")
        string_bytes_length = len(string_bytes)

        return bytearray(struct.pack("I%ss" % string_bytes_length, string_bytes_length, string_bytes))

    @staticmethod
    def create_new_directory(name: str) -> bytearray:
        code = 0x01
        data = bytearray()

        data.append(code)
        data.extend(Protocol.string_to_bytes(name))

        return data

    @staticmethod
    def send_new_file(name: str, size: int, chunk_size: int, checksum: str) -> bytearray:
        code = 0x02
        data = bytearray()
        data.append(code)

        file = {"name": name, "size": size, "chunk_size": chunk_size, "checksum": checksum}

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
