import sys
import socket
import logging

from client.network.core.client import Client
from client.network.protocol.protocol import Protocol

from client.core.controllers.directory_controller import DirectoryController
from client.core.controllers.file_controller import FileController

from client.core.models.directory import Directory
from client.core.models.file import File

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

    def main(self) -> None:
        try:
            self.client.connect()
        except socket.error as e:
            logging.CRITICAL("Impossible to connect on %s:%s", self.client.ip_address, self.client.port)
            logging.WARNING("Connection error:", e.strerror)

            self.exit(1)

        logging.INFO("Receiving chunk size from server...")
        self.chunk_size = self.receive_packet(Protocol.receive_chunk_size)

        logging.INFO("Chunk size received successfully")
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
        logging.INFO("Sending file %s..." % file.path)

        self.client.send(Protocol.send_create_new_file(file.name, file.size, file.checksum))

    def send_directory(self, current_directory: Directory):
        self.client.send(Protocol.send_create_new_directory(current_directory.name))

        for file in current_directory.files_list:
            self.send_file(file)

        for sub_directory in current_directory.sub_directories_list:
            self.send_directory(sub_directory)
