import socket


class Client:

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.ip_address, self.port))
        except socket.error as e:
            return e

        return None

    def send(self, data: bytes) -> None:
        self.socket.send(data)

    def receive(self) -> bytes:
        return self.socket.recv(1024)
