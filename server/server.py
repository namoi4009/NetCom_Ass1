import socket
import threading

MAX_CLIENTS = 20

HOST = "192.168.1.137"
PORT = 65432

clients = []

def connect_client(conn, addr):
    print(f"Connected by {addr}")
    while True:
        try:
            message = conn.recv(1024).decode()
            if not message:
                break
            print(f"{addr} says: {message}")
            broadcast(message, conn)
        except:
            continue

    # When a client disconnects
    print(f"Disconnected: {addr}")
    clients.remove(conn)
    conn.close()

def broadcast(message, connection):
    for client in clients:
        if client != connection:
            try:
                client.sendall(message.encode())
            except:
                client.close()
                
# Server would need to handle requests for specific pieces
def handle_piece_request(conn, piece_index):
    # Here you would fetch and send the requested piece
    pass
                
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print("Server started on {HOST}. Listening for connections...")

        while True:
            conn, addr = server.accept()
            clients.append(conn)
            thread = threading.Thread(target=connect_client, args=(conn, addr))
            thread.start()
        
if __name__ == "__main__":
    main()