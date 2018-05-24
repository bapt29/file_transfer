import socket
import threading
import signal
import sys


class Server:

    def __init__(self, port):
        self.port = port

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
        while self.running:
            data = client_socket.recv(1024)

            if not data:
                break

            print(data.decode())

        client_socket.close()
        print("Client with address", client_address, "disconnected")

    def stop(self):
        self.running = False
        sys.exit(0)


if __name__ == '__main__':
    server = Server(1234)
    server.serve()
