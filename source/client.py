import os
import socket
from bencode import bencode, bdecode
import threading
import json
import queue

# Constants
BUFFER_SIZE = 1024
CHAR_TYPE = 'utf-8'
SERVER_PORT = 6789
SERVER_IP = "192.168.31.118"
CHUNK_SIZE = 524288
SERVER_ADDR = (SERVER_IP, SERVER_PORT)
TORRENT_STRUCTURE = {}
MEMORY_DIR = "Chunks"
TORRENT_FILE = "torrent_file"

# Variables
running = True
server_connected = False
connected_clients = {}


client_set = []


this_client_info = {
    "ip": socket.gethostbyname(socket.gethostname()),
    "listen_port": 9011,  #  to listen to other client's command
    "chunk_status": {},
    "downloaded": 0,
    "uploaded": 0
}
send_server_port = 9012  #  to send command to other clients or server
send_client_port = 9013    # to receive data from other

listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.bind((this_client_info["ip"], this_client_info["listen_port"]))

send_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_server_socket.bind((this_client_info["ip"], send_server_port))

send_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_client_socket.bind((this_client_info["ip"],send_client_port))

request_sender_socket = {} 

# client-server communication cmds:
def connect_server():  
    global server_connected
    send_server_socket.connect(SERVER_ADDR)
    send_server_socket.send(bencode(this_client_info).encode(CHAR_TYPE))
    received_msg = send_server_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))
    server_connected = True
    get_client_set()


def get_client_set():  
    global client_set
    if not check_server_connected():
        return
    send_server_socket.send(bencode("get_client_set").encode(CHAR_TYPE))
    received_msg = send_server_socket.recv(2048).decode(CHAR_TYPE)
    client_set = bdecode(received_msg)


def update_status_to_server():  
    if not check_server_connected():
        return
    send_server_socket.send(
        bencode("update_status_to_server"+" "+bencode(this_client_info)).encode(CHAR_TYPE))
    received_msg = send_server_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))
    get_client_set()


def disconnect_server():  
    global server_connected
    if not check_server_connected():
        return
    send_server_socket.send(bencode("disconnect_server").encode(CHAR_TYPE))
    received_msg = send_server_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))
    send_server_socket.close()
    server_connected = False


def quit_torrent():  
    global running, server_connected
    if not check_server_connected():
        connect_server()
    send_server_socket.send(bencode("quit_torrent").encode(CHAR_TYPE))
    received_msg = send_server_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))
    running = False
    send_server_socket.close()


# client-client communication request cmds:
def connect_client(target_client_IP, target_client_port):  
    print(target_client_IP, target_client_port)
    target_client_addr = (target_client_IP, int(target_client_port))
    
    request_sender_socket[f"{target_client_IP} {target_client_port}"] = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    current_request_sender_socket = request_sender_socket[f"{target_client_IP} {target_client_port}"]
    current_request_sender_socket.connect(target_client_addr)
    
    current_request_sender_socket.send(bencode(this_client_info).encode(
        CHAR_TYPE))
    received_msg = current_request_sender_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))
    connected_clients[f"{target_client_IP} {target_client_port}"] = True


def ping(target_client_IP, target_client_port):
    if not check_target_client_connected(target_client_IP, target_client_port):
        return
    current_request_sender_socket = request_sender_socket[f"{target_client_IP} {target_client_port}"]
    current_request_sender_socket.send(
        bencode(f"ping {target_client_IP} {target_client_port}").encode(CHAR_TYPE))
    received_msg = current_request_sender_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))


def request_download(target_client_ip, target_client_port, missing_chunk):
    if not check_target_client_connected(target_client_ip, target_client_port):
        return
    current_request_sender_socket = request_sender_socket[f"{target_client_ip} {target_client_port}"]
    current_request_sender_socket.send(bencode(
        f"request_download {target_client_ip} {target_client_port} {missing_chunk}").encode(CHAR_TYPE))
    received_msg = bdecode(
        current_request_sender_socket.recv(2048).decode(CHAR_TYPE))
    print(received_msg)
    if received_msg != f"File {missing_chunk} not found!":
        file_path = os.path.join(MEMORY_DIR, missing_chunk)
        with open(file_path, 'wb') as file:
            data = current_request_sender_socket.recv(1024*1024)
            file.write(data)
        print("File received successfully!")
        this_client_info["downloaded"] += 1
        this_client_info["chunk_status"] = update_chunk_status()
    else:
        print("failed to request download!")


def disconnect_client(target_client_IP, target_client_port):  
    if not check_target_client_connected(target_client_IP, target_client_port):
        return
    current_request_sender_socket = request_sender_socket[f"{target_client_IP} {target_client_port}"]
    current_request_sender_socket.send(
        bencode(f"disconnect_client {target_client_IP} {target_client_port}").encode(CHAR_TYPE))
    received_msg = current_request_sender_socket.recv(2048).decode(CHAR_TYPE)
    print(bdecode(received_msg))
    connected_clients[f"{target_client_IP} {target_client_port}"] = False


# client functionality cmds:
def check_server_connected():  
    if not server_connected:
        print("client is not connected to server")
    return server_connected


def check_target_client_connected(target_client_IP, target_client_port):  
    if not connected_clients[f"{target_client_IP} {target_client_port}"]:
        print(
            f"Target client[{target_client_IP},{target_client_port}] is not connected to current client[{this_client_info['ip']} {send_client_socket}]")
    return connected_clients[f"{target_client_IP} {target_client_port}"]


def see_this_client_info():  
    print_dict(this_client_info)


def see_client_set():  
    for client in client_set:
        print("\n")
        print_dict(client)
        print("\n")


def see_connected():  
    print(connected_clients)


def see_torrent_struct():
    print("\n")
    print_dict(TORRENT_STRUCTURE)
    print("\n")


def see_chunk_status():  
    this_client_info["chunk_status"] = update_chunk_status()
    print("\n")
    print_dict(this_client_info["chunk_status"])
    print("\n")


def merge_chunks(target_file):  
    if not check_merge_file(target_file):
        print("Not enough chunks to merge")
        return
    files = os.listdir(MEMORY_DIR)

    files.sort()

    with open(os.path.join(MEMORY_DIR, target_file), 'wb') as merged_file:
        for file_name in files:
            if file_name[:len(target_file)] != target_file:
                continue
            with open(os.path.join(MEMORY_DIR, file_name), 'rb') as chunk_file:
                merged_file.write(chunk_file.read())
        print("Merge complete!")


def check_merge_file(file_name):  
    this_client_info["chunk_status"] = update_chunk_status()
    chunk_status = this_client_info["chunk_status"]
    merge = True
    for chunk in TORRENT_STRUCTURE[file_name]:
        if chunk_status[chunk] == 0:
            merge = False
            break
    return merge

# Init client
def client_init():
    global SERVER_IP, SERVER_PORT, CHUNK_SIZE, TORRENT_STRUCTURE
    TORRENT_STRUCTURE = read_torrent_file()
    this_client_info["chunk_status"] = update_chunk_status()
    
# client Connection Handling
def handle_request_client_connection(this_request_handler_socket, request_client_addr):  
    request_client_info_msg = this_request_handler_socket.recv(
        BUFFER_SIZE).decode(CHAR_TYPE)
    request_client_info = bdecode(request_client_info_msg)
    this_client_ip = this_client_info["ip"]
    this_client_listen_port = this_client_info["listen_port"]
    request_client_ip = request_client_info['ip']
    request_client_port = request_client_info['listen_port']
    print(f"\n[NEW CONNECTION] {request_client_ip} connected.")
    
    this_request_handler_socket.send(bencode(
        f"client[{this_client_ip},{this_client_listen_port}] established connection to client[{request_client_ip},{request_client_port}]").encode(CHAR_TYPE))  # send to client

    connected_clients[f"{request_client_ip} {request_client_port}"] = True

    while connected_clients[f"{request_client_ip} {request_client_port}"]:
        received_msg = this_request_handler_socket.recv(BUFFER_SIZE).decode(CHAR_TYPE)
        if received_msg:
            msg = bdecode(received_msg)
            print(f"Sender[{request_client_ip},{request_client_port}] {msg}")

            msg_parts = msg.split()
            match msg_parts[0]:
                case "ping":
                    if (len(msg_parts) != 3):
                        print(
                            "Invalid CHAR_TYPE! Please provide both request client IP and port.")
                        return
                    if (not msg_parts[1] or not msg_parts[2]):
                        print(
                            "Invalid CHAR_TYPE! Please provide both request client IP and port.")
                    else:
                        print(
                            f"[PING RECEIVED] from client[{request_client_ip},{request_client_port}]")
                        this_request_handler_socket.send(bencode(
                            f"client[{this_client_ip},{this_client_listen_port}] received ping from client[{request_client_ip},{request_client_port}]").encode(CHAR_TYPE))  # send to client

                case "request_download":
                    file_path = os.path.join(MEMORY_DIR, msg_parts[3])
                    if os.path.exists(file_path):  # if chunk exists on server
                        print(
                            f"Sending {msg_parts[3]} to client[{this_client_info['ip']},{this_client_info['listen_port']}]...")
                        this_request_handler_socket.send(bencode(
                            f"client[{this_client_ip},{this_client_listen_port}] starts uploading chunk {msg_parts[3]} to client[{msg_parts[1]},{msg_parts[2]}]").encode(CHAR_TYPE))  # send to client
                        send_file(this_request_handler_socket,
                                  file_path)  # send chunk
                        print(f"{msg_parts[3]} sent successfully!")
                        this_client_info["uploaded"] += 1
                    else:
                        print(f"File {msg_parts[3]} does not exist.")
                        this_request_handler_socket.send(
                            bencode(f"File {msg_parts[3]} not found!").encode(CHAR_TYPE))

                # [target_client_IP] [target_client_port] 
                case "disconnect_client":
                    if (len(msg_parts) != 3):
                        print(
                            "Invalid CHAR_TYPE! Please provide both request client IP and port.")
                        return
                    if (not msg_parts[1] or not msg_parts[2]):
                        print(
                            "Invalid CHAR_TYPE! Please provide both request client IP and port.")
                    else:
                        print(
                            f"[REQUEST client DISCONNECTED THIS client] {msg_parts[1]}")
                        this_request_handler_socket.send(bencode(
                            f"client[{this_client_ip},{this_client_listen_port}] disconnected from client[{msg_parts[1]},{msg_parts[2]}]").encode(CHAR_TYPE))  # send to client

                        connected_clients[f"{request_client_ip} {request_client_port}"] = False
                        this_request_handler_socket.close()
                case _:
                    this_request_handler_socket.send(
                        bencode("Invalid command").encode(CHAR_TYPE))
    this_request_handler_socket.close()

# File Handler

def read_torrent_file():
    torrent_file_path = os.path.join(MEMORY_DIR, TORRENT_FILE)
    
    try:
        with open(torrent_file_path, 'r') as file:
            torrent_structure = json.load(file)
        return torrent_structure
    except FileNotFoundError:
        print("The torrent file could not be found.")
        return None
    except json.JSONDecodeError:
        print("Failed to parse the torrent file. Ensure it is in valid JSON format.")
        return None


def init_chunk_status():
    torrent_structure = TORRENT_STRUCTURE
    chunk_status = {}
    for file_name in torrent_structure:
        for chunk_name in torrent_structure[file_name]:
            chunk_status[chunk_name] = 0
    return chunk_status


def update_chunk_status():
    memory_dir = MEMORY_DIR
    chunk_status = init_chunk_status()
    for filename in os.listdir(memory_dir):
        filepath = os.path.join(memory_dir, filename)
        if os.path.isfile(filepath) and filename in chunk_status:  # 512kb in bytes
            chunk_status[filename] = 1
    return chunk_status

def print_dict(dictionary):
    for key in dictionary:
        print(f"{key}: {dictionary[key]}")

def get_socket_address(sock):
    # Get the socket's address
    address = sock.getsockname()
    return address

def send_file(client_socket, file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
        client_socket.sendall(data)

# Mainly Threading Functions
def command_handler(user_input):
    global running, server_connected, connected_clients
    user_input_parts = user_input.split()

    match user_input_parts[0]:

        case "connect_server":
            connect_server()
        case "get_client_set":
            get_client_set()
        case "update_status_to_server":
            update_status_to_server()
        case "disconnect_server":
            disconnect_server()
        case "quit_torrent":
            quit_torrent()

        case "connect_client":
            if (len(user_input_parts) != 3):
                print("Invalid CHAR_TYPE! Please provide both request client IP and port.")
                return
            if (not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid CHAR_TYPE! Please provide both target client IP and port.")
            else:
                connect_client(user_input_parts[1], int(user_input_parts[2]))
        case "ping":
            if (len(user_input_parts) != 3):
                print("Invalid CHAR_TYPE! Please provide both request client IP and port.")
                return
            if (not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid CHAR_TYPE! Please provide both target client IP and port.")
            else:
                ping(user_input_parts[1], int(user_input_parts[2]))

        case "request_download":
            if (len(user_input_parts) != 4):
                print("Invalid CHAR_TYPE! Please provide both request client IP and port.")
                return
            if (not user_input_parts[1] or not user_input_parts[2] or not user_input_parts[3]):
                print("Invalid CHAR_TYPE! Please provide both target client IP and port.")
            else:
                request_download(user_input_parts[1], int(
                    user_input_parts[2]), user_input_parts[3])
        case "disconnect_client": 
            if (len(user_input_parts) != 3):
                print("Invalid CHAR_TYPE! Please provide both request client IP and port.")
                return
            if (not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid CHAR_TYPE! Please provide both target client IP and port.")
            else:
                disconnect_client(user_input_parts[1], int(user_input_parts[2]))


        case "check_server_connected":
            check_server_connected()
        case "check_target_client_connected": 
            if (len(user_input_parts) != 3):
                print("Invalid CHAR_TYPE! Please provide both request client IP and port.")
                return
            if (not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid CHAR_TYPE! Please provide both target client IP and port.")
            else:
                check_target_client_connected(
                    user_input_parts[1], user_input_parts[2])
        case "see_this_client_info":
            see_this_client_info()
        case "see_client_set":
            see_client_set()
        case "see_connected":
            see_connected()
        case "see_torrent_struct":
            see_torrent_struct()
        case "see_chunk_status":
            see_chunk_status()
        case "merge_chunks":
            if (len(user_input_parts) != 2):
                print("Invalid CHAR_TYPE! Please provide file name.")
                return
            if (not user_input_parts[1]):
                print("Invalid CHAR_TYPE! Please provide file name.")
            else:
                merge_chunks(user_input_parts[1])
        case _:
            pass


def command_thread(commands_queue):
    while running:
        try:
            command = commands_queue.get(timeout=2)
            command_handler(command)
            if (command == "quit_torrent"):
                quit()
        except queue.Empty:
            client_ip = this_client_info["ip"]
            client_port = this_client_info["listen_port"]
            print(f"[{client_ip},{client_port}] ", end='')
            user_input = input()
            command_handler(user_input)
            if (user_input == "quit_torrent"):
                quit()


if __name__ == "__main__":
    client_init()
    commands_queue = queue.Queue()
    
    # Order that run automatically
    commands_queue.put("connect_server")
    
    command_thrd = threading.Thread(target=command_thread)
    command_thrd.start()
    listening_socket.listen()
    
    while running:
        request_handler_socket, request_client_addr = listening_socket.accept()
        thread = threading.Thread(target=handle_request_client_connection, args=(
            request_handler_socket, request_client_addr))  # create a "listening client" thread
        thread.start()
        print(f"[ACTIVE CONNECTION] {threading.active_count()-1}")
