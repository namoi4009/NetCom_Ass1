import socket
import threading
from bencode import bencode, bdecode

# Server Constants
HEADER = 1024
PORT = 7001
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
PEER_SET = []

# Create server socket
tracker_listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tracker_listening_socket.bind(ADDR)

def handle_peer_connection(peer_socket, peer_addr):
    """Handle each connected peer."""
    peer_info_msg = peer_socket.recv(HEADER).decode(FORMAT)
    peer_info = bdecode(peer_info_msg)
    peer_ip = peer_info['ip']
    peer_port = peer_info['listen_port']
    print(f"\n[NEW CONNECTION] {peer_ip} connected.")

    peer_socket.send(bencode(f"Tracker established connection to Peer[{peer_ip},{peer_port}]").encode(FORMAT))

    # Maintain connection
    while True:
        msg = peer_socket.recv(HEADER).decode(FORMAT)
        if msg:
            process_message(peer_socket, peer_ip, peer_port, msg)
        else:
            break

    peer_socket.close()

def process_message(peer_socket, peer_ip, peer_port, msg):
    """Process messages from peers."""
    command = bdecode(msg)
    command_type = command.split()[0]
    if command_type == "/get_peer_set":
        peer_socket.send(bencode(PEER_SET).encode(FORMAT))
    elif command_type == "/update_status_to_tracker":
        peer_socket.send(bencode(f"Tracker updated Peer[{peer_ip},{peer_port}] status").encode(FORMAT))
    elif command_type == "/disconnect_tracker":
        peer_socket.send(bencode(f"Peer[{peer_ip},{peer_port}] disconnected from tracker").encode(FORMAT))
    elif command_type == "/quit_torrent":
        PEER_SET.remove(peer_info)
        peer_socket.send(bencode(f"Peer[{peer_ip},{peer_port}] quited torrent").encode(FORMAT))
    else:
        peer_socket.send(bencode("Invalid command").encode(FORMAT))

def start_server():
    """Start server to listen for connections."""
    tracker_listening_socket.listen()
    print(f"[LISTENING] Tracker is listening on {SERVER}")
    while True:
        peer_socket, peer_addr = tracker_listening_socket.accept()
        thread = threading.Thread(target=handle_peer_connection, args=(peer_socket, peer_addr))
        thread.start()

if __name__ == "__main__":
    print("[STARTING] Tracker is starting")
    start_server()