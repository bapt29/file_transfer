import struct
import json


class Handler:

    def __init__(self, client_socket, client_address):
        self.base_path = "/home/user/"  # put this in config file

        self.client_socket = client_socket
        self.client_address = client_address

        self.main_buffer = bytearray()
        self.packet_buffer = bytearray()

        self.missing_packet_bytes = int()

        self.deserialized_packet = str()

    def handle(self) -> None:
        if not self.get_last_packet(): # Incomplete packet
            return

        self.packet_deserialize()
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

    def packet_deserialize(self):
        self.deserialized_packet = json.loads(self.packet_buffer[5:])

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


    def create_new_file(self):
        pass

    def receive_file_chunk(self):
        pass

    def end_of_file(self):
        pass

    def end_of_directory(self):
        pass

    def transfer_abort(self):
        pass
