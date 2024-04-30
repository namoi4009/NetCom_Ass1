import os
import socket
import threading
from bencode import bencode, bdecode
import json

# Client Constants
HEADER = 1024
FORMAT = 'utf-8'
TRACKER_PORT = 0
TRACKER_IP = ""
CHUNK_SIZE = 0
TRACKER_ADDR = (socket.gethostbyname(socket.gethostname()), 7001)
TORRENT_STRUCTURE = {}
MEMORY_DIR = "Memory"
TORRENT_FILE = "torrent_file"

# Initialize this peer's information
this_peer_info = {
    "ip": socket.gethostbyname(socket.gethostname()),
    "listen_port": 7000,  # Port for incoming peer commands
    "chunk_status": {},  # File chunk availability
    "downloaded": 0,  # Total downloaded chunks
    "uploaded": 0  # Total uploaded chunks
}

# Port settings for different functionalities
send_tracker_port = 5000  # Port for sending commands to the tracker
send_peer_port = 6000  # Port for sending commands to other peers

# Socket Setup
listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.bind((this_peer_info["ip"], this_peer_info["listen_port"]))

send_tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_tracker_socket.bind((this_peer_info["ip"], send_tracker_port))

send_peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_peer_socket.bind((this_peer_info["ip"], send_peer_port))

# Runtime variables
running = True
tracker_connected = False
connected_peers = {}
request_sender_socket = {}

def connect_tracker():
    """Establish connection with the tracker."""
    send_tracker_socket.connect(TRACKER_ADDR)
    send_tracker_socket.send(bencode(this_peer_info).encode(FORMAT))
    response = send_tracker_socket.recv(2048).decode(FORMAT)
    print(bdecode(response))
    tracker_connected = True
    get_peer_set()

def get_peer_set():
    """Request the current set of peers from the tracker."""
    if not tracker_connected:
        print("Not connected to tracker.")
        return
    send_tracker_socket.send(bencode("/get_peer_set").encode(FORMAT))
    response = send_tracker_socket.recv(2048).decode(FORMAT)
    Peer_set = bdecode(response)

def update_status_to_tracker():
    """Send updated status to the tracker."""
    if not tracker_connected:
        print("Not connected to tracker.")
        return
    send_tracker_socket.send(bencode("/update_status_to_tracker " + bencode(this_peer_info)).encode(FORMAT))
    response = send_tracker_socket.recv(2048).decode(FORMAT)
    print(bdecode(response))
    get_peer_set()

def disconnect_tracker():
    """Disconnect from the tracker."""
    if not tracker_connected:
        print("Not connected to tracker.")
        return
    send_tracker_socket.send(bencode("/disconnect_tracker").encode(FORMAT))
    response = send_tracker_socket.recv(2048).decode(FORMAT)
    print(bdecode(response))
    send_tracker_socket.close()
    tracker_connected = False

def quit_torrent():
    """Quit the torrent network."""
    if not tracker_connected:
        connect_tracker()
    send_tracker_socket.send(bencode("/quit_torrent").encode(FORMAT))
    response = send_tracker_socket.recv(2048).decode(FORMAT)
    print(bdecode(response))
    running = False
    send_tracker_socket.close()
        
# peer-to-peer
        
def connect_to_peer(peer_ip, peer_port):
    """Connect to a target peer and establish a communication channel."""
    target_peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_peer_socket.connect((peer_ip, peer_port))
    target_peer_socket.send(bencode(this_peer_info).encode(FORMAT))
    response = target_peer_socket.recv(2048).decode(FORMAT)
    connected_peers[(peer_ip, peer_port)] = target_peer_socket
    print(f"Connected to peer {peer_ip}:{peer_port} - {bdecode(response)}")

def disconnect_from_peer(peer_ip, peer_port):
    """Disconnect from a connected peer."""
    if (peer_ip, peer_port) in connected_peers:
        connected_peers[(peer_ip, peer_port)].close()
        del connected_peers[(peer_ip, peer_port)]
        print(f"Disconnected from peer {peer_ip}:{peer_port}")
    else:
        print("No such peer connected.")

def request_file_from_peer(peer_ip, peer_port, file_chunk):
    """Request a specific file chunk from a connected peer."""
    if (peer_ip, peer_port) not in connected_peers:
        print("Peer is not connected. Connecting...")
        connect_to_peer(peer_ip, peer_port)
    
    peer_socket = connected_peers[(peer_ip, peer_port)]
    request_message = f"/request_download {file_chunk}"
    peer_socket.send(bencode(request_message).encode(FORMAT))
    response = peer_socket.recv(2048).decode(FORMAT)
    handle_file_transfer(peer_socket, bdecode(response), file_chunk)

def handle_file_transfer(peer_socket, message, file_chunk):
    """Handle file transfer from a peer."""
    if "start transferring" in message:
        file_path = os.path.join(MEMORY_DIR, file_chunk)
        with open(file_path, 'wb') as file:
            while True:
                data = peer_socket.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f"Received {file_chunk} successfully.")
    else:
        print("Failed to start transfer:", message)

def send_file_to_peer(peer_socket, file_chunk):
    """Send a file chunk to a requesting peer."""
    file_path = os.path.join(MEMORY_DIR, file_chunk)
    if not os.path.exists(file_path):
        peer_socket.send(bencode("File not found").encode(FORMAT))
        return
    
    peer_socket.send(bencode("start transferring").encode(FORMAT))
    with open(file_path, 'rb') as file:
        data = file.read(1024)
        while data:
            peer_socket.send(data)
            data = file.read(1024)
    print(f"Sent {file_chunk} successfully.")

def handle_peer_connection(client_socket, client_address):
    """Handle incoming connections and requests from other peers."""
    while True:
        request = client_socket.recv(HEADER).decode(FORMAT)
        if not request:
            break
        process_peer_request(client_socket, request)
    client_socket.close()

def process_peer_request(client_socket, request):
    """Process requests from connected peers."""
    request_args = bdecode(request).split()
    command = request_args[0]
    if command == "/request_download":
        send_file_to_peer(client_socket, request_args[1])
    elif command == "/disconnect":
        client_socket.close()
        print(f"Peer {client_socket.getpeername()} disconnected.")

def command_thread():
    """Thread for handling user input commands."""
    while running:
        command = input(f"[{this_peer_info['ip']},{this_peer_info['listen_port']}] > ")
        command_handler(command)

def command_handler(command):
    """Handle commands input by the user."""
    parts = command.split()
    if command == "/connect_tracker":
        connect_tracker()
    elif command.startswith("/get_peer_set"):
        get_peer_set()
    elif command.startswith("/update_status_to_tracker"):
        update_status_to_tracker()
    elif command == "/disconnect_tracker":
        disconnect_tracker()
    elif command == "/quit_torrent":
        quit_torrent()
    elif parts[0] == "/connect_peer":
        connect_to_peer(parts[1], int(parts[2]))
    elif parts[0] == "/disconnect_peer":
        disconnect_from_peer(parts[1], int(parts[2]))
    elif parts[0] == "/request_file":
        request_file_from_peer(parts[1], int(parts[2]), parts[3])
    elif parts[0] == "/quit":
        global running
        running = False
        print("Quitting...")
    else:
        print("Unknown command.")

if __name__ == "__main__":
    threading.Thread(target=command_thread).start()
    listening_socket.listen()
    while running:
        client_socket, addr = listening_socket.accept()
        threading.Thread(target=handle_peer_connection, args=(client_socket, addr)).start()