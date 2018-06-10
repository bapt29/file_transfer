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

    def __init__(self, ip_address, port, verbosity_level=None, files_path_list=None, directories_path_list=None):
        self.client = Client(ip_address, port)

        self.files_path_list = files_path_list
        self.directories_path_list = directories_path_list

        self.files_list = list()
        self.directories_list = list()

        self.logger = logging.getLogger("main")
        
        if verbosity_level == 3:
            self.logger.setLevel(logging.DEBUG)
        elif verbosity_level == 2:
            self.logger.setLevel(logging.INFO)
        elif verbosity_level == 1:
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.CRITICAL)

        if files_path_list is None and directories_path_list is None:
            self.logger.critical("No paths were entered")
            self.exit(1)

        self.chunk_size = None

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
            self.logger.critical("Unexpected error while connecting to the server")
            self.logger.error("Invalid packet received")
            self.logger.debug("Packet type: %s" % error)

            self.exit(1)
        except socket.error as error:
            self.logger.critical("Connection error")
            self.logger.error("Socket error: %s" % error.strerror)

            self.exit(1)
        except:
            self.logger.critical("Unexpected error occurred: ", sys.exc_info()[0])
            raise
            self.exit(1)
        else:
            return response

    def abort_file_transfer(self, file_name: str) -> None:
        self.client.send(Protocol.send_file_transfer_abort(file_name))

        if not self.receive_packet(Protocol.receive_confirmation_packet):
            self.logger.debug("abort file transfer confirmation failed")
            self.logger.critical("Server error")
            sys.exit(1)

    def main(self) -> None:
        try:
            self.client.connect()
        except socket.error as e:
            self.logger.critical("Impossible to connect on %s:%s" % (self.client.ip_address, self.client.port))
            self.logger.warning("Connection error: %s" % e.strerror)

            self.exit(1)

        self.logger.info("Receiving chunk size from server...")
        self.chunk_size = self.receive_packet(Protocol.receive_chunk_size)
        self.logger.info("Done.")

        self.logger.debug("Chunk size: %d Ko" % self.chunk_size)

        if self.files_path_list is not None:
            FileController.from_path_list(self.files_path_list, self.files_list, self.chunk_size)
            self.send_single_files()

        if self.directories_path_list is not None:
            DirectoryController.from_path_list(self.directories_path_list, self.directories_list, self.chunk_size)
            self.send_directories()

        self.exit(0)

    def send_single_files(self):
        self.logger.info("Sending single files...")

        for file in self.files_list:
            self.send_file(file)

    def send_directories(self):
        self.logger.info("Sending directories...")

        for main_directory in self.directories_list:
            self.send_directory(main_directory)

    def send_file(self, file: File):
        FileController.open(file)
        self.file_view.display(file)

        self.client.send(Protocol.send_create_new_file(file.name, file.size, file.checksum))

        if not self.receive_packet(Protocol.receive_confirmation_packet):
            self.logger.critical("File could not be sent")
            return

        response = True

        while response:
            response = self.send_file_chunk(file)

    def send_file_chunk(self, file: File):
        while True:
            read_error = 0

            try:
                FileController.read(file)
            except EndOfFile:
                self.logger.debug("send eof packet")
                self.client.send(Protocol.send_end_of_file(file.name))

                if not self.receive_packet(Protocol.receive_confirmation_packet):
                    self.logger.debug("confirmation failed")
                    self.logger.critical("Server error")
                    self.exit(1)

                if not self.receive_packet(Protocol.receive_file_integrity_confirmation):
                    self.logger.critical("File integrity check failed: trying to send file again...")
                    self.send_file(file)

                return False

            except IOError as error:
                if read_error < 3:
                    read_error += 1
                    continue

                self.logger.info("File read error: ", error.strerror)

                self.abort_file_transfer(file.name)
                self.logger.critical("File transfer aborted: could not read the file")

                return False
            else:
                integrity_confirmed = False
                limit = 0

                while not integrity_confirmed:
                    if limit > 5:
                        self.logger.debug("chunk integrity confirmation failed")

                        self.abort_file_transfer(file.name)
                        self.logger.critical("File transfer aborted: integrity check failure")

                        return False

                    FileController.update_last_chunk_time(file)
                    self.client.send(Protocol.send_file_chunk(file.name,
                                                              file.current_chunk,
                                                              file.current_chunk_data,
                                                              file.current_chunk_checksum))

                    integrity_confirmed = self.receive_packet(Protocol.receive_file_chunk_integrity_confirmation)
                    self.file_view.update(file)
                    limit += 1

                return True

    def send_directory(self, current_directory: Directory):
        self.client.send(Protocol.send_create_new_directory(current_directory.name))

        if not self.receive_packet(Protocol.receive_confirmation_packet):
            self.logger.critical("Directory %s could not be sent" % current_directory.path)
            return

        for file in current_directory.files_list:
            self.send_file(file)

        for sub_directory in current_directory.sub_directories_list:
            self.send_directory(sub_directory)

        self.client.send(Protocol.send_end_of_directory(current_directory.name))

        if not self.receive_packet(Protocol.receive_confirmation_packet):
            self.logger.critical("Directory could not be sent")
            return


if __name__ == '__main__':
    import argparse

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--ip_address", "-i", help="server ip address", required=True)
    argument_parser.add_argument("--port", "-p", help="server port", type=int, required=True)
    argument_parser.add_argument("--verbosity", "-v", help="verbosity level", action="count")
    argument_parser.add_argument("--files_path", "-f", nargs='*', help="Files paths to transfer")
    argument_parser.add_argument("--directories_path", "-d", nargs='*', help="Directories paths to transfer")

    args = argument_parser.parse_args()

    Main(args.ip_address, args.port, args.verbosity, args.files_path, args.directories_path)
