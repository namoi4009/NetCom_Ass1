import socket
import threading

# Server configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5001
BUFFER_SIZE = 1024

# Placeholder for the file to be served, this could be replaced with actual file reading logic
file_parts = [
    b"This is part 1 of the file.",
    b"This is part 2 of the file.",
    b"This is part 3 of the file.",
]

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    while True:
        try:
            data = conn.recv(BUFFER_SIZE).decode()
            if data == "EXIT":
                break
            part_no = int(data)
            conn.send(file_parts[part_no])
        except Exception as e:
            print(f"Error: {e}")
            break
    conn.close()

def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((SERVER_HOST, SERVER_PORT))
        s.listen()
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")
        
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    server()
