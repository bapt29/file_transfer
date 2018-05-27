import sys
import socket
import logging

from client.network.core.client import Client
from client.network.protocol.protocol import Protocol

from client.core.models.directory import Directory
from client.core.models.file import File

from client.core.views.file_view import FileView

from client.core.controllers.directory_controller import DirectoryController
from client.core.controllers.file_controller import FileController

from client.errors.directory_errors import *
from client.errors.file_errors import *
from client.errors.network_errors import *


class Main:

    def __init__(self, ip_address, port, verbosity_level):
        self.client = Client(ip_address, port)

        if verbosity_level == 3:
            logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)
        elif verbosity_level == 2:
            logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)
        elif verbosity_level == 1:
            logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.ERROR)
        else:
            logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.CRITICAL)

        self.chunk_size = None

        self.directory_controller = None
        self.file_controller = None

        self.file_view = FileView

        self.main()

    def __del__(self):
        self.client.disconnect()

    def exit(self, error_code: int):
        del self
        sys.exit(error_code)

    def receive_packet(self, protocol_function):
        try:
            response = protocol_function(self.client.receive())
        except InvalidPacket as error:
            logging.CRITICAL("Unexpected error while connecting to the server")
            logging.ERROR("Invalid packet received")
            logging.DEBUG("Packet type: %s" % error)

            self.exit(1)
        except socket.error as error:
            logging.CRITICAL("Connection error")
            logging.ERROR("Socket error: ", error.strerror)

            self.exit(1)
        except:
            logging.CRITICAL("Unexpected error occurred")

            self.exit(1)
        else:
            return response

    def abort_file_transfer(self, file_name: str) -> None:
        self.client.send(Protocol.send_file_transfer_abort(file_name))

        if not self.receive_packet(Protocol.receive_confirmation_packet):
            logging.DEBUG("abort file transfer confirmation failed")
            logging.CRITICAL("Server error")
            sys.exit(1)

    def main(self) -> None:
        try:
            self.client.connect()
        except socket.error as e:
            logging.CRITICAL("Impossible to connect on %s:%s", self.client.ip_address, self.client.port)
            logging.WARNING("Connection error:", e.strerror)

            self.exit(1)

        logging.INFO("Receiving chunk size from server...", end="")
        self.chunk_size = self.receive_packet(Protocol.receive_chunk_size)
        logging.INFO(" done.")

        logging.DEBUG("Chunk size: %d Ko" % self.chunk_size)

        self.file_controller = FileController(self.chunk_size)
        self.directory_controller = DirectoryController(self.chunk_size)

        self.send_single_files()
        self.send_directories()

    def send_single_files(self):
        logging.INFO("Sending single files...")

        for file in self.file_controller.files_list:
            self.send_file(file)

    def send_directories(self):
        logging.INFO("Sending directories...")

        for main_directory in self.directory_controller.root_directories_list:
            self.send_directory(main_directory)

    def send_file(self, file: File):
        self.file_controller.open(file)
        self.file_view.display(file)

        self.client.send(Protocol.send_create_new_file(file.name, file.size, file.checksum))

        if not self.receive_packet(Protocol.receive_confirmation_packet):
            logging.CRITICAL("File could not be sent")
            return

        response = True

        while response:
            self.file_view.update(file)
            response = self.send_file_chunk(file)

    def send_file_chunk(self, file: File):
        while True:
            read_error = 0

            try:
                self.file_controller.read(file)
            except EndOfFile:
                logging.DEBUG("send eof packet")
                self.client.send(Protocol.send_end_of_file(file.name))

                if not self.file_controller(Protocol.receive_confirmation_packet):
                    logging.DEBUG("confirmation failed")
                    logging.CRITICAL("Server error")
                    sys.exit(1)

            except IOError as error:
                if read_error < 3:
                    read_error += 1
                    continue

                logging.INFO("File read error: ", error.strerror)

                self.abort_file_transfer(file.name)
                logging.CRITICAL("File transfer aborted: could not read the file")

                return False
            else:
                integrity_confirmed = False
                limit = 0

                while not integrity_confirmed:
                    if limit > 5:
                        logging.DEBUG("chunk integrity confirmation failed")

                        self.abort_file_transfer(file.name)
                        logging.CRITICAL("File transfer aborted: integrity check failure")

                        return False

                    self.client.send(Protocol.send_file_chunk(file.name,
                                                              file.current_chunk,
                                                              file.current_chunk_data,
                                                              file.current_chunk_checksum))

                    integrity_confirmed = self.receive_packet(Protocol.receive_file_chunk_integrity_confirmation)
                    limit += 1

                return True

    def send_directory(self, current_directory: Directory):
        self.client.send(Protocol.send_create_new_directory(current_directory.name))

        for file in current_directory.files_list:
            self.send_file(file)

        for sub_directory in current_directory.sub_directories_list:
            self.send_directory(sub_directory)

        self.client.send(Protocol.send_end_of_directory(current_directory.name))
