import socket
import threading
import json

class Server:
    def __init__(self, host='127.0.0.1', port=65432):
        self.address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.address)
        self.server_socket.listen()
        print(f"Server listening on {host}:{port}")
        self.client_map = {}
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        print(f"Connected by {addr}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                if message['type'] == 'announce':
                    with self.lock:
                        self.client_map[addr] = message['files']
                    print(f"Received file list from {addr}")
                elif message['type'] == 'request':
                    requested_file = message['file']
                    with self.lock:
                        available_clients = [
                            client for client, files in self.client_map.items()
                            if requested_file in files
                        ]
                    response = json.dumps({'clients': available_clients}).encode('utf-8')
                    conn.sendall(response)
        finally:
            with self.lock:
                del self.client_map[addr]
            conn.close()
            print(f"Disconnected {addr}")

    def run(self):
        while True:
            conn, addr = self.server_socket.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    server = Server()
    server.run()
