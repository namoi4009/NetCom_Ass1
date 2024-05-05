import threading
import socket
from bencode import bencode, bdecode

BUFFER_SIZE = 1024
SERVER_PORT = 6789
HOST_NAME = socket.gethostbyname(socket.gethostname())
SERVER_ADDRESS = (HOST_NAME, SERVER_PORT)
ENCODING = 'utf-8'
THREAD_LOCK = threading.Lock()
PEER_LIST = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(SERVER_ADDRESS)


def manage_client_connection(client_socket, client_address):
    print(client_address)
    client_message = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    client_data = bdecode(client_message)
    client_ip = client_data['ip']
    client_listen_port = client_data['listen_port']
    print(f"\n[NEW CONNECTION] {client_ip} connected.")

    client_socket.send(bencode(
        f"Server established connection to Client[{client_ip},{client_listen_port}]").encode(ENCODING))

    if client_data not in PEER_LIST:
        PEER_LIST.append(client_data)

    is_connected = True
    while is_connected:
        message_received = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
        if message_received:
            parsed_message = bdecode(message_received)
            print(f"[{client_ip},{client_listen_port}] {parsed_message}")

            command_parts = parsed_message.split()
            match command_parts[0]:
                case "/get_peers":
                    print(f"[PEER LIST] {PEER_LIST}")
                    client_socket.send(bencode(PEER_LIST).encode(ENCODING))
                case "/update_status":
                    print(f"[PEER UPDATE] {client_ip},{client_listen_port}")
                    updated_client_data = bdecode(command_parts[1])
                    refresh_peer_list(updated_client_data, PEER_LIST)
                    client_socket.send(bencode(
                        f"server updated Client[{client_ip},{client_listen_port}] status").encode(ENCODING))
                case "/disconnect":
                    print(
                        f"[CLIENT DISCONNECTED] {client_ip},{client_listen_port}")
                    client_socket.send(bencode(
                        f"Client[{client_ip},{client_listen_port}] disconnected").encode(ENCODING))
                    is_connected = False
                case "/exit":
                    print(f"[CLIENT EXITED] {client_ip},{client_listen_port}")
                    client_socket.send(
                        bencode(f"Client[{client_ip},{client_listen_port}] exited").encode(ENCODING))
                    PEER_LIST.remove(client_data)
                    is_connected = False
                case _:
                    client_socket.send(
                        bencode("U\n").encode(ENCODING))
    client_socket.close()


def refresh_peer_list(new_client_data, client_list):
    for idx, data in enumerate(client_list):
        if new_client_data["ip"] == data["ip"] and new_client_data["listen_port"] == data["listen_port"]:
            client_list[idx] = new_client_data
            break


def run_server():
    server_socket.listen()
    print(f"[LISTENING] server is listening on {HOST_NAME}")
    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(
            target=manage_client_connection, args=(client_socket, client_address))
        client_thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


if __name__ == "__main__":
    print("[STARTING] server is starting")
    run_server()
