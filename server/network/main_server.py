import socket
import threading
import signal
import sys

from server.network.handler import Handler
from server.core.configuration import Configuration


class Server:

    def __init__(self):
        #  self.config = Configuration("config.ini")

        #  self.port = self.config.read_config("DEFAULT", "port")
        #  self.chunk_size = self.config.read_config("DEFAULT", "chunk_size")
        #  self.default_path = self.config.read_config("DEFAULT", "path")

        self.port = 1234
        self.chunk_size = 15
        self.default_path = "/home/user/transferred_files/"

        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.running = True
        signal.signal(signal.SIGTERM, self.stop)

    def serve(self):
        self.main_socket.bind(("0.0.0.0", self.port))
        self.main_socket.listen(1)

        print("Server now listening on port", self.port)

        try:
            while True:
                self.accept_connection()
        except KeyboardInterrupt:
            self.stop()

    def accept_connection(self):
        client_socket, client_address = self.main_socket.accept()

        print("Client connected with address:", client_address)

        client_thread = threading.Thread(target=self.new_client, args=(client_socket, client_address,))
        client_thread.start()

    def new_client(self, client_socket, client_address):
        handler = Handler(client_socket, client_address, self.chunk_size, self.default_path)
        handler.send_chunk_size()

        while self.running:
            data = client_socket.recv(1024)

            if not data:
                break

            handler.main_buffer.extend(bytearray(data))
            handler.handle()

        client_socket.close()
        print("Client with address", client_address, "disconnected")

    def stop(self):
        self.running = False
        sys.exit(0)


if __name__ == '__main__':
    server = Server()
    server.serve()
