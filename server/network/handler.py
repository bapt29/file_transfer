import struct
import json
import os

from server.core.models.file import File
from server.core.managers.file_manager import FileManager

from server.network.protocol import Protocol

from server.errors.file_errors import *


class Handler:

    def __init__(self, client_socket, client_address, chunk_size):
        self.base_path = "/home/user/"  # put this in config file
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
            self.transfer_abort()
        else:
            return  # fix that case

    def packet_json_deserialize(self) -> dict:
        return json.loads(self.packet_buffer[5:])

    def packet_string_decode(self) -> str:
        return self.packet_buffer[5:].decode()

    def get_last_packet(self) -> bool:
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
        new_directory_path = self.current_path+self.packet_string_decode()

        os.mkdir(new_directory_path)
        self.current_path = new_directory_path+"/"

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

    def receive_file_chunk(self):
        file_chunk = self.packet_json_deserialize()

        try:
            FileManager.write_new_chunk(self.current_file,
                                        file_chunk["number"],
                                        file_chunk["size"],
                                        file_chunk["data"],
                                        file_chunk["checksum"])
        except InvalidChunkNumber:
            self.client_socket.send(Protocol.confirmation_packet(False))
            return
        except ChecksumDoesNotMatch:
            self.client_socket.send(Protocol.file_chunk_integrity_confirmation(False))
            return

        self.client_socket.send(Protocol.file_chunk_integrity_confirmation(True))

    def end_of_file(self):
        self.client_socket.send(Protocol.confirmation_packet(True))

        if not FileManager.is_file_checksum_match(self.current_file):
            self.client_socket.send(Protocol.file_integrity_confirmation(False))

            file_name = self.current_file.name

            del self.current_file
            self.current_file = None
            os.remove(self.current_path+file_name)

            return

        del self.current_file
        self.current_file = None

    def end_of_directory(self):
        self.current_path = self.current_path.split("/")[-1]

    def transfer_abort(self):
