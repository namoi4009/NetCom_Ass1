import os
from time import sleep
import threading
import socket
from bencode import bencode,bdecode


HEADER = 1024

SERVER = "192.168.240.1"
PORT = 65432
ADDR = (SERVER,PORT)

FORMAT = 'utf-8'
LOCK = threading.Lock()
PEER_SET=[]

tracker_listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tracker_listening_socket.bind(ADDR)


def handle_peer_connection(peer_handler_socket, peer_addr):  # Run for each Peer connected

    print(peer_addr)
    peer_info_msg=peer_handler_socket.recv(HEADER).decode(FORMAT)
    peer_info=bdecode(peer_info_msg)
    peer_ip=peer_info['ip']
    peer_port=peer_info['listen_port']
    print(f"\n[NEW CONNECTION] {peer_ip} connected.")

    peer_handler_socket.send(bencode(f"Tracker established connection to Peer[{peer_ip},{peer_port}]").encode(FORMAT)) # send to peer

    # Update Peer Set when new Peer connects
    if not peer_info in PEER_SET:
        PEER_SET.append(peer_info)

    connected = True
    while connected:
        received_msg = peer_handler_socket.recv(HEADER).decode(FORMAT)
        if received_msg:
            msg = bdecode(received_msg)
            print(f"[{peer_ip},{peer_port}] {msg}")

            msg_parts=msg.split()
            match msg_parts[0]:
                case "/get_peer_set":
                    print(f"[PEER SET] {PEER_SET}")
                    peer_handler_socket.send(bencode(PEER_SET).encode(FORMAT))  # send PEER SET string
                    connected = True
                case "/update_status_to_tracker":
                    print(f"[PEER UPDATE] {peer_ip},{peer_port}")
                    received_peer_info=bdecode(msg_parts[1])
                    update_peer_set(received_peer_info,PEER_SET)
                    peer_handler_socket.send(bencode(f"Tracker updated Peer[{peer_ip},{peer_port}] status").encode(FORMAT))
                case "/disconnect_tracker":
                    print(f"[PEER DISCONNECTED TRACKER] {peer_ip},{peer_port}")
                    peer_handler_socket.send(bencode(f"Peer[{peer_ip},{peer_port}] disconnected from tracker").encode(FORMAT))  # send to peer
                    connected = False
                case "/quit_torrent":
                    print(f"[PEER QUITED TORRENT] {peer_ip},{peer_port}")
                    peer_handler_socket.send(bencode(f"Peer[{peer_ip},{peer_port}] quited torrent").encode(FORMAT))  # send to peer
                    PEER_SET.remove(peer_info)
                    connected=False
                case _:
                    peer_handler_socket.send(bencode("Invalid command").encode(FORMAT))
    peer_handler_socket.close()

def update_peer_set(new_peer_info,peer_set):
    for i in range(len(peer_set)):
        peer_info=peer_set[i]
        if new_peer_info["ip"] == peer_info["ip"] and new_peer_info["listen_port"] == peer_info["listen_port"]:
            peer_set[i] = new_peer_info
            break


def start():
    tracker_listening_socket.listen()
    print(f"[LISTENING] Tracker is listening on {SERVER}")
    while True:
        peer_handler_socket,peer_addr = tracker_listening_socket.accept() # detect a client connect
        thread = threading.Thread(target=handle_peer_connection,args=(peer_handler_socket,peer_addr)) # create a "listening peer" thread
        thread.start()
        print(f"[ACTIVE CONNECTION] {threading.active_count()-1}")
        

if __name__ == "__main__":
    print("[STARTING] Tracker is starting")
    start()
