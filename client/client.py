import socket

# Server configuration
SERVER_HOST = 'localhost'
SERVER_PORT = 5001
BUFFER_SIZE = 1024

def request_file_part(part_no):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall(str(part_no).encode())
        data = s.recv(BUFFER_SIZE)
        return data

if __name__ == "__main__":
    parts = []
    for i in range(3):
        part = request_file_part(i)
        parts.append(part)
        print(f"Received part {i}: {part.decode()}")

    full_file = b''.join(parts)
    print(f"Full file content: {full_file.decode()}")
