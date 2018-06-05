import struct
import binascii
import json
import os

from server.core.models.file import File
from server.core.managers.file_manager import FileManager

from server.network.protocol import Protocol

from server.errors.file_errors import *


class Handler:

    def __init__(self, client_socket, client_address, chunk_size, default_path):
        self.base_path = default_path
        self.current_path = self.base_path

        self.client_socket = client_socket
        self.client_address = client_address

        self.main_buffer = bytearray()
        self.packet_buffer = bytearray()

        self.missing_packet_bytes = int()

        self.current_file = None

        self.chunk_size = chunk_size

    def handle(self) -> None:
        if not self.get_last_packet():  # Incomplete packet
            return

        code = self.packet_buffer[0]

        if code == 0x01:
            self.create_new_directory()
        elif code == 0x02:
            self.create_new_file()
        elif code == 0x03:
            self.receive_file_chunk()
        elif code == 0x04:
            self.end_of_file()
        elif code == 0x05:
            self.end_of_directory()
        elif code == 0x06:
            self.file_transfer_abort()
        else:
            return

    def packet_json_deserialize(self) -> dict:
        return json.loads(self.packet_buffer[5:])

    def packet_string_decode(self) -> str:
        packet_string = self.packet_buffer[5:].decode()

        return packet_string

    def get_last_packet(self) -> bool:  # TODO: test this method
        if len(self.packet_buffer) == 0:
            if len(self.main_buffer) >= 5:
                packet_size = struct.unpack("I", self.main_buffer[1:5])[0]

                if len(self.main_buffer) >= packet_size+5:
                    self.packet_buffer.extend(self.main_buffer[:packet_size+5])
                    del self.main_buffer[:packet_size+5]

                    return True
                else:
                    self.packet_buffer.extend(self.main_buffer[:-1])
                    self.missing_packet_bytes = (packet_size+5) - len(self.main_buffer)
                    del self.main_buffer[:]

                    return False
        else:
            if len(self.main_buffer) >= self.missing_packet_bytes:
                self.packet_buffer.extend(self.main_buffer[:self.missing_packet_bytes])
                del self.main_buffer[:self.missing_packet_bytes]

                return True
            else:
                self.packet_buffer.extend(self.main_buffer[:-1])
                self.missing_packet_bytes -= len(self.main_buffer)
                del self.main_buffer[:]

                return False

    def create_new_directory(self):
        packet_string = self.packet_string_decode()

        if len(packet_string) == 0:
            self.client_socket.send(Protocol.confirmation_packet(False))
            return

        new_directory_path = self.current_path+packet_string

        os.mkdir(new_directory_path)
        self.current_path = new_directory_path+"/"
        del self.packet_buffer[:]

    def create_new_file(self):
        if self.current_file is not None:
            self.client_socket.send(Protocol.confirmation_packet(False))
            return

        file_dict = self.packet_json_deserialize()
        file_path = self.current_path+file_dict["name"]

        self.current_file = File(file_path,
                                 file_dict["size"],
                                 file_dict["checksum"],
                                 self.chunk_size)

        self.client_socket.send(Protocol.confirmation_packet(True))
        del self.packet_buffer[:]

    def receive_file_chunk(self):
        file_chunk = self.packet_json_deserialize()

        try:
            FileManager.write_new_chunk(self.current_file,
                                        file_chunk["number"],
                                        file_chunk["size"],
                                        binascii.unhexlify(file_chunk["data"]),
                                        file_chunk["checksum"])
        except InvalidChunkNumber:
            self.client_socket.send(Protocol.confirmation_packet(False))
        except ChecksumDoesNotMatch:
            self.client_socket.send(Protocol.file_chunk_integrity_confirmation(False))
        else:
            self.client_socket.send(Protocol.file_chunk_integrity_confirmation(True))

        del self.packet_buffer[:]

    def end_of_file(self):
        self.client_socket.send(Protocol.confirmation_packet(True))

        if not FileManager.is_file_checksum_match(self.current_file):
            self.client_socket.send(Protocol.file_integrity_confirmation(False))

            file_name = self.current_file.name

            del self.current_file
            self.current_file = None
            os.remove(self.current_path+file_name)
            del self.packet_buffer[:]

            return

        del self.current_file
        self.current_file = None
        del self.packet_buffer[:]

    def end_of_directory(self):
        self.current_path = "/".join(self.current_path.split("/")[:-2])+"/"
        del self.packet_buffer[:]

    def file_transfer_abort(self):
        del self.current_file
        os.remove(self.current_path+self.current_file.name)
        self.current_file = None
        del self.packet_buffer[:]

    def send_chunk_size(self):
        data = bytearray()
        data.append(0x01)

        data.extend(bytearray(struct.pack("I", self.chunk_size)))
        self.client_socket.send(data)
