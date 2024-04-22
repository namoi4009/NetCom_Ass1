import socket
import threading
import json
import sys

class Client:
    def __init__(self, host='127.0.0.1', port=65432, files=None):
        self.server_address = (host, port)
        self.files = files if files else []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.server_address)
        self.send_announce()

    def send_announce(self):
        message = json.dumps({'type': 'announce', 'files': self.files})
        self.socket.sendall(message.encode('utf-8'))

    def request_file(self, filename):
        message = json.dumps({'type': 'request', 'file': filename})
        self.socket.sendall(message.encode('utf-8'))
        data = self.socket.recv(1024)
        response = json.loads(data.decode('utf-8'))
        print(f"Clients with {filename}: {response['clients']}")

    def run(self):
        while True:
            filename = input("Enter filename to request: ")
            if filename.lower() == 'exit':
                break
            self.request_file(filename)
        self.socket.close()

if __name__ == "__main__":
    files = sys.argv[1:] if len(sys.argv) > 1 else []
    client = Client(files=files)
    client.run()