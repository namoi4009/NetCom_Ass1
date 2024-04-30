import os
from time import sleep
import threading
import socket
from bencode import bencode,bdecode


HEADER = 1024
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)
FORMAT = 'utf-8'
LOCK = threading.Lock()
PEER_SET=[]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def handle_client(conn, addr):  # Run for each Peer connected
    print(f"\n[NEW CONNECTION] {addr} connected.")

    # Receive peer information
    peer_info_length = conn.recv(HEADER).decode(FORMAT)
    peer_info_length = int(peer_info_length)
    peer_info = bdecode(conn.recv(peer_info_length).decode(FORMAT))

    # Receive chunk directory information
    chunk_dir_length = conn.recv(HEADER).decode(FORMAT)
    chunk_dir_length = int(chunk_dir_length)
    chunk_directory = bdecode(conn.recv(chunk_dir_length).decode(FORMAT))

    # Update Peer Set when new Peer connects
    PEER_SET.append({"peer_info": peer_info, "chunk_directory": chunk_directory})

    conn.send("Updated Peer Set".encode(FORMAT))  # send "Updated Peer Set"

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = bdecode(conn.recv(msg_length).decode(FORMAT))
            print(f"[{addr}] {msg}")
            match msg:
                case "/quit":
                    print(f"[PEER LEFT] {addr}")
                    conn.send("Disconnected".encode(FORMAT))  # send "Disconnected"
                    connected = False
                case "/get_peer_set":
                    print(f"[PEER SET] {PEER_SET}")
                    for peer in PEER_SET:
                        print(f"[Peer Info] {peer['peer_info']}")
                        print(f"[Chunks] {os.listdir(peer['chunk_directory'])}")
                    conn.send(bencode(PEER_SET).encode(FORMAT))  # send PEER SET string
                    connected = True
                case "/update_status":
                    print(f"[PEER UPDATE] {addr}")
                    ###########################################
                    # UPDATE PEER SET HERE
                    # TODO
                    ###########################################
                    connected = True
                case _:
                    conn.send("Invalid command".encode(FORMAT))
                    connected = True
    #################################################
    # Update Peer Set when Peer disconnect
    PEER_SET.remove({"peer_info": peer_info, "chunk_directory": chunk_directory})
    #################################################
    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Tracker is listening on {SERVER}")
    while True:
        conn,addr = server.accept() # detect a client connect
        thread = threading.Thread(target=handle_client,args=(conn,addr)) # create a "listening peer" thread
        thread.start()
        print(f"\n[ACTIVE CONNECTION] {threading.active_count()-1}")
        

if __name__ == "__main__":
    print("[STARTING] Tracker is starting")
    start()
