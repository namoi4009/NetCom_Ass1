import socket
import threading
import signal

class Server:
    def __init__(self, host='127.0.0.1', port=65432):
        self.address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.address)
        self.server_socket.listen()
        self.active_connections = []
        self.is_running = True
        print(f"Server listening on {host}:{port}")

    def handle_client(self, conn, addr):
        print(f"Connected by {addr}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                # Process data here
                print(f"Data from {addr}: {data.decode()}")
        finally:
            print(f"Disconnected {addr}")
            conn.close()

    def run(self):
        self.server_socket.settimeout(1)  # Set timeout to make the accept call non-blocking
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
                self.active_connections.append(conn)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                self.shutdown_server()

    def shutdown_server(self):
        print("Shutting down server...")
        self.is_running = False
        for conn in self.active_connections:
            conn.close()
        self.server_socket.close()

if __name__ == "__main__":
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        server.shutdown_server()
