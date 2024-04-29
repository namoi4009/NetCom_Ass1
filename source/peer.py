import os
import socket
from bencode import bencode,bdecode
import threading
import json

###########################################START################################################
#                                   PEER'S GLOBAL VARIABLES                                    #
###########################################START################################################

# Constants
HEADER = 1024
FORMAT = 'utf-8'
TRACKER_PORT=0
TRACKER_IP = "" # get from torrent file
CHUNK_SIZE = 0
TRACKER_ADDR = None
TORRENT_STRUCTURE={}
MEMORY_DIR="Memory"
TORRENT_FILE="torrent_file"

# Variables
running=True
tracker_connected=False
connected_peers={}


Peer_set=[]



this_peer_info={
    # "peer_id": peer_id,
    "ip": socket.gethostbyname(socket.gethostname()),
    "listen_port": 7000, # used to listen to other peer's command
    "chunk_status": {}, # {"filesplit_part1":True,"filesplit_part2":False,...} True=exist in memory; False=missing
    "downloaded": 0,
    "uploaded": 0
}
send_tracker_port=5000 # used to send command to other peers or tracker
send_peer_port=6000

listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.bind((this_peer_info["ip"], this_peer_info["listen_port"]))


send_tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_tracker_socket.bind((this_peer_info["ip"],send_tracker_port))

send_peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
send_peer_socket.bind((this_peer_info["ip"],send_peer_port))

request_sender_socket={} # "[ip] [port]": socket



###########################################END##################################################
#                                   PEER'S GLOBAL VARIABLES                                    #
###########################################END##################################################

###########################################START################################################
#                                   PEER COMMAND FUNCTIONS                                     #
###########################################START################################################

# peer-tracker communication cmds: 

def connect_tracker(): # done
    global tracker_connected
    send_tracker_socket.connect(TRACKER_ADDR)                           # 1/ establish connection to tracker
    send_tracker_socket.send(bencode(this_peer_info).encode(FORMAT))                  # 2/ send bencoded peer_info to tracker
    received_msg = send_tracker_socket.recv(2048).decode(FORMAT)       # 3/ tracker response "Tracker established connection to Peer[peer_ip]"
    print(bdecode(received_msg))
    tracker_connected = True                                        # 4/ tracker_connected = True 
    get_peer_set()                                                  # 5/ run /get_peer_set

def get_peer_set(): # done
    global Peer_set
    if not check_tracker_connected():                               # 1/ run /check_tracker_connected. Go to step 2/ if returned True
        return
    send_tracker_socket.send(bencode("/get_peer_set").encode(FORMAT))                 # 2/ send "/get_peer_set" (string msg) to tracker.
    received_msg = send_tracker_socket.recv(2048).decode(FORMAT)       # 3/ tracker response bencoded tracker's PEER_SET (string)
    Peer_set=bdecode(received_msg)                                  # 4/ bdecode tracker response (list if dictionaries [{},{},{}] ) and update peer's PEER_SET

def update_status_to_tracker(): # done
    if not check_tracker_connected():                               # 1/ run /check_tracker_connected. Go to step 2/ if returned True
        return
    send_tracker_socket.send(bencode("/update_status_to_tracker"+" "+bencode(this_peer_info)).encode(FORMAT))                 # 2/ send "/update_status_to_tracker" [bencoded Peer_info] (string msg) to tracker
    received_msg = send_tracker_socket.recv(2048).decode(FORMAT)       # 3/ Tracker response: "Tracker updated Peer[peer_ip] status"
    print(bdecode(received_msg))
    get_peer_set()

def disconnect_tracker(): # done
    global tracker_connected
    if not check_tracker_connected():                               # 1/ run /check_tracker_connected. Go to step 2/ if returned True
        return
    send_tracker_socket.send(bencode("/disconnect_tracker").encode(FORMAT))           # 2/ send bencoded "/disconnect_tracker" (string msg) to tracker 
    received_msg = send_tracker_socket.recv(2048).decode(FORMAT)       # 3/ tracker response "Peer[peer_id] disconnected from tracker"
    print(bdecode(received_msg))
    send_tracker_socket.close()
    tracker_connected = False                                       # 4/ tracker_connected = False

def quit_torrent(): # done
    global running,tracker_connected
    if not check_tracker_connected():                               # 1/ run /check_tracker_connected. Run /connect_tracker then Go to step 2/ if returned False
        connect_tracker()
    send_tracker_socket.send(bencode("/quit_torrent").encode(FORMAT))                 # 2/ send bencoded "/quit_torrent" (string msg) to tracker 
    received_msg = send_tracker_socket.recv(2048).decode(FORMAT)       # 3/ tracker response "Peer[peer_id] quited torrent"
    print(bdecode(received_msg))
    running=False                                                   # 4/ leave the torrent and won't upload/ download chunks (peer.py program stops running)
    send_tracker_socket.close()
    


# peer-peer communication request cmds:

def connect_peer(target_peer_IP,target_peer_port): # done
    print(target_peer_IP,target_peer_port)
    target_peer_addr= (target_peer_IP,int(target_peer_port))
    ################################################################
    request_sender_socket[f"{target_peer_IP} {target_peer_port}"]=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    current_request_sender_socket=request_sender_socket[f"{target_peer_IP} {target_peer_port}"]
    current_request_sender_socket.connect(target_peer_addr) 
    ################################################################
    current_request_sender_socket.send(bencode(this_peer_info).encode(FORMAT))                           # 1/ establish connection to target peer
    received_msg = current_request_sender_socket.recv(2048).decode(FORMAT)           # 2/ Target peer response: "Peer[target_peer_ip,target_peer_port] established connection to Peer[this_peer_ip]"
    print(bdecode(received_msg))
    connected_peers[f"{target_peer_IP} {target_peer_port}"]=True; 
    
def ping(target_peer_IP,target_peer_port):
    if not check_target_peer_connected(target_peer_IP,target_peer_port):                               # 1/ run /check_tracker_connected. Go to step 2/ if returned True
        return
    current_request_sender_socket=request_sender_socket[f"{target_peer_IP} {target_peer_port}"]
    current_request_sender_socket.send(bencode(f"/ping {target_peer_IP} {target_peer_port}").encode(FORMAT))  # 2/ send bencoded "/ping [target_peer_IP] [target_peer_port]" to [target_peer_IP,target_peer_port]
    received_msg = current_request_sender_socket.recv(2048).decode(FORMAT)
    print(bdecode(received_msg))
    

def request_download(target_peer_ip,target_peer_port,missing_chunk):
    if not check_target_peer_connected(target_peer_ip,target_peer_port):                               # 1/ run /check_tracker_connected. Go to step 2/ if returned True
        return
    current_request_sender_socket=request_sender_socket[f"{target_peer_ip} {target_peer_port}"]
    current_request_sender_socket.send(bencode(f"/request_download {target_peer_ip} {target_peer_port} {missing_chunk}").encode(FORMAT))  # 2/ send bencoded "/request_download [target_peer_IP] [target_peer_port] [missing_chunk]" to [target_peer_IP,target_peer_port]
    received_msg = bdecode(current_request_sender_socket.recv(2048).decode(FORMAT))
    print(received_msg)
    if received_msg!=f"File {missing_chunk} not found!":
        file_path = os.path.join(MEMORY_DIR, missing_chunk) 
        with open(file_path, 'wb') as file:
            data = current_request_sender_socket.recv(1024*1024) # recieve chunks from server
            file.write(data)
        print("File received successfully!")
        this_peer_info["downloaded"]+=1
        this_peer_info["chunk_status"]=update_chunk_status()
    else:
        print("failed to request download!")
    

def disconnect_peer(target_peer_IP,target_peer_port): # done
    if not check_target_peer_connected(target_peer_IP,target_peer_port):                               # 1/ run /check_tracker_connected. Go to step 2/ if returned True
        return
    current_request_sender_socket=request_sender_socket[f"{target_peer_IP} {target_peer_port}"]
    current_request_sender_socket.send(bencode(f"/disconnect_peer {target_peer_IP} {target_peer_port}").encode(FORMAT))  # 2/ send bencoded "/disconnect_peer [target_peer_IP] [target_peer_port]" to [target_peer_IP,target_peer_port]
    received_msg = current_request_sender_socket.recv(2048).decode(FORMAT)
    print(bdecode(received_msg))
    connected_peers[f"{target_peer_IP} {target_peer_port}"]=False


# peer functionality cmds:

def check_tracker_connected(): # done
    if not tracker_connected:
        print("Peer is not connected to tracker")
    return tracker_connected

def check_target_peer_connected(target_peer_IP,target_peer_port): #done
    if not connected_peers[f"{target_peer_IP} {target_peer_port}"]:
        print(f"Target Peer[{target_peer_IP},{target_peer_port}] is not connected to current Peer[{this_peer_info['ip']} {send_peer_socket}]")
    return connected_peers[f"{target_peer_IP} {target_peer_port}"]

def see_this_peer_info(): # done
    print_dict(this_peer_info)

def see_peer_set(): # done
    for peer in Peer_set:
        print("==========================================")
        print_dict(peer) # 1/ print Peer_set
        print("==========================================")

def see_connected(): # done
    print(connected_peers)

def see_torrent_struct():
    print("==========================================")
    print_dict(TORRENT_STRUCTURE)
    print("==========================================")

def see_chunk_status(): # done
    this_peer_info["chunk_status"]=update_chunk_status()
    print("==========================================")
    print_dict(this_peer_info["chunk_status"])
    print("==========================================")

def merge_chunks(target_file): # done
    if not check_merge_file(target_file): 
        print("Not enough chunks to merge")
        return
    # Get a list of all files in the folder
    files = os.listdir(MEMORY_DIR)
    
    # Sort the files to ensure they are merged in the correct order
    files.sort()
    
    # Open the target file in binary write mode
    with open(os.path.join(MEMORY_DIR, target_file), 'wb') as merged_file:
        # Iterate over each file in the folder
        for file_name in files:
            if file_name[:len(target_file)] != target_file:
                continue 
            # Open the chunk file in binary read mode
            with open(os.path.join(MEMORY_DIR, file_name), 'rb') as chunk_file:
                # Read the contents of the chunk file and write them to the target file
                merged_file.write(chunk_file.read())
        print("Merge complete!")

def check_merge_file(file_name): # done
    this_peer_info["chunk_status"]=update_chunk_status()
    chunk_status=this_peer_info["chunk_status"]
    merge=True
    for chunk in TORRENT_STRUCTURE[file_name]:
        if chunk_status[chunk]==0:
            merge=False
            break
    return merge
###########################################END##################################################
#                                   PEER COMMAND FUNCTIONS                                     #
###########################################END##################################################

###########################################START################################################
#                                   PEER LISTENING FUNCTIONS                                   #
###########################################START################################################

def handle_request_peer_connection(this_request_handler_socket,request_peer_addr): # done
    request_peer_info_msg=this_request_handler_socket.recv(HEADER).decode(FORMAT)
    request_peer_info=bdecode(request_peer_info_msg)
    this_peer_ip=this_peer_info["ip"]
    this_peer_listen_port=this_peer_info["listen_port"]
    request_peer_ip=request_peer_info['ip']
    request_peer_port=request_peer_info['listen_port']
    print(f"\n[NEW CONNECTION] {request_peer_ip} connected.") # 1/ establish connection to [request_peer_ip]

    # 2/ send "Peer[this_peer_ip,this_peer_port] established connection to Peer[request_peer_ip,request_peer_port]" (string msg) to [request_peer_ip]
    this_request_handler_socket.send(bencode(f"Peer[{this_peer_ip},{this_peer_listen_port}] established connection to Peer[{request_peer_ip},{request_peer_port}]").encode(FORMAT)) # send to peer
    # 3/ connected_peers[requested_peer_IP]=True
    connected_peers[f"{request_peer_ip} {request_peer_port}"]=True

    # 4/ Start a while-loop thread to listen to [requested_peer_ip,request_peer_port]
    while connected_peers[f"{request_peer_ip} {request_peer_port}"]:
        received_msg = this_request_handler_socket.recv(HEADER).decode(FORMAT)
        if received_msg:
            msg = bdecode(received_msg)
            print(f"Sender[{request_peer_ip},{request_peer_port}] {msg}")

            msg_parts=msg.split()
            match msg_parts[0]:
                case "/ping":
                    if (len(msg_parts)!=3):
                        print("Invalid format! Please provide both request peer IP and port.")
                        return
                    if(not msg_parts[1] or not msg_parts[2]):
                        print("Invalid format! Please provide both request peer IP and port.")
                    else:
                        print(f"[PING RECEIVED] from Peer[{request_peer_ip},{request_peer_port}]")
                        this_request_handler_socket.send(bencode(f"Peer[{this_peer_ip},{this_peer_listen_port}] received ping from Peer[{request_peer_ip},{request_peer_port}]").encode(FORMAT))  # send to peer
                
                case "/request_download":
                    file_path = os.path.join(MEMORY_DIR, msg_parts[3])
                    if os.path.exists(file_path): # if chunk exists on server
                        print(f"Sending {msg_parts[3]} to Peer[{this_peer_info['ip']},{this_peer_info['listen_port']}]...")
                        this_request_handler_socket.send(bencode(f"Peer[{this_peer_ip},{this_peer_listen_port}] starts uploading chunk {msg_parts[3]} to Peer[{msg_parts[1]},{msg_parts[2]}]").encode(FORMAT)) # send to peer
                        send_file(this_request_handler_socket, file_path) # send chunk
                        print(f"{msg_parts[3]} sent successfully!")
                        this_peer_info["uploaded"]+=1
                    else:
                        print(f"File {msg_parts[3]} does not exist.")
                        this_request_handler_socket.send(bencode(f"File {msg_parts[3]} not found!").encode(FORMAT))
                    
                case "/disconnect_peer":# [target_peer_IP] [target_peer_port] # done
                    # 1/ check if input is valid
                    if (len(msg_parts)!=3):
                        print("Invalid format! Please provide both request peer IP and port.")
                        return
                    if(not msg_parts[1] or not msg_parts[2]):
                        print("Invalid format! Please provide both request peer IP and port.")
                    else:
                        print(f"[REQUEST PEER DISCONNECTED THIS PEER] {msg_parts[1]}")
                        # 2/ send "Peer[this_peer_id,this_peer_port] disconnected from Peer[target_peer_ip,target_peer_port]"
                        this_request_handler_socket.send(bencode(f"Peer[{this_peer_ip},{this_peer_listen_port}] disconnected from Peer[{msg_parts[1]},{msg_parts[2]}]").encode(FORMAT))  # send to peer
                        connected_peers[f"{request_peer_ip} {request_peer_port}"] = False # 3/
                        this_request_handler_socket.close()
                case _:
                    this_request_handler_socket.send(bencode("Invalid command").encode(FORMAT))
    this_request_handler_socket.close()

###########################################END##################################################
#                                   PEER LISTENING FUNCTIONS                                   #
###########################################END##################################################

###########################################START################################################
#                                       PEER INIT FUNCTION                                     #
###########################################START################################################

def peer_init():
    global TRACKER_IP, TRACKER_PORT, CHUNK_SIZE, TORRENT_STRUCTURE
    TRACKER_IP, TRACKER_PORT, CHUNK_SIZE = read_torrent_file_part1()
    TORRENT_STRUCTURE = read_torrent_file_part2()  # Move this line here
    this_peer_info["chunk_status"] = update_chunk_status()
    see_chunk_status()

###########################################END##################################################
#                                       PEER INIT FUNCTION                                     #
###########################################END##################################################

###########################################START################################################
#                                       OTHER FUNCTIONS                                        #
###########################################START################################################

def read_torrent_file_part1():
    global TRACKER_ADDR
    torrent_file=TORRENT_FILE
    memory_dir=MEMORY_DIR
    # Construct the full path to the torrent file
    torrent_file_path = os.path.join(memory_dir, torrent_file)

    # Read the first three lines of the torrent file
    with open(torrent_file_path, 'r') as file:
        lines = file.readlines()[:3]

        # Extract tracker_ip, tracker_port, and chunk_size
        tracker_ip = lines[0].strip()
        tracker_port = int(lines[1].strip())
        chunk_size = int(lines[2].strip())
    TRACKER_ADDR=(tracker_ip,tracker_port)
    # Return the extracted values
    return tracker_ip, tracker_port, chunk_size

def read_torrent_file_part2():
    torrent_file=TORRENT_FILE
    memory_dir=MEMORY_DIR
    # Construct the full path to the torrent file
    torrent_file_path = os.path.join(memory_dir, torrent_file)

    # Read the JSON data from the torrent file starting from line 4
    with open(torrent_file_path, 'r') as file:
        # Skip the first three lines
        for _ in range(3):
            next(file)
        # Load the JSON data
        torrent_structure = json.load(file)

    # Return the torrent structure dictionary
    return torrent_structure

def init_chunk_status():
    torrent_structure=TORRENT_STRUCTURE
    chunk_status={}
    for file_name in torrent_structure:
        for chunk_name in torrent_structure[file_name]:
            chunk_status[chunk_name]=0
    return chunk_status

def update_chunk_status():
    memory_dir=MEMORY_DIR
    chunk_status=init_chunk_status()
    for filename in os.listdir(memory_dir):
        filepath = os.path.join(memory_dir, filename)
        if os.path.isfile(filepath) and filename in chunk_status:  # 512kb in bytes
            chunk_status[filename]=1
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

###########################################END##################################################
#                                       OTHER FUNCTIONS                                        #
###########################################END##################################################

def command_handler(user_input):
    global running, tracker_connected, connected_peers
    user_input_parts=user_input.split()

    match user_input_parts[0]:

        # peer-tracker communication cmds: 
        case "/connect_tracker":
            connect_tracker()
        case "/get_peer_set":
            get_peer_set()
        case "/update_status_to_tracker":
            update_status_to_tracker()
        case "/disconnect_tracker":
            disconnect_tracker()
        case "/quit_torrent":
            quit_torrent()

        # peer-peer communication request cmds:
        case "/connect_peer":# [target_peer_IP] [target_peer_port]
            if (len(user_input_parts)!=3):
                print("Invalid format! Please provide both request peer IP and port.")
                return
            if(not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid format! Please provide both target peer IP and port.")
            else:
                connect_peer(user_input_parts[1],int(user_input_parts[2]))
        case "/ping":# [target_peer_IP] [target_peer_port]
            if (len(user_input_parts)!=3):
                print("Invalid format! Please provide both request peer IP and port.")
                return
            if(not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid format! Please provide both target peer IP and port.")
            else:
                ping(user_input_parts[1],int(user_input_parts[2]))
        case "/request_download":# [target_peer_IP] [target_peer_port] [missing_chunk]
            if (len(user_input_parts)!=4):
                print("Invalid format! Please provide both request peer IP and port.")
                return
            if(not user_input_parts[1] or not user_input_parts[2] or not user_input_parts[3]):
                print("Invalid format! Please provide both target peer IP and port.")
            else:
                request_download(user_input_parts[1],int(user_input_parts[2]),user_input_parts[3])
        case "/disconnect_peer":# [target_peer_IP] [target_peer_port]
            if (len(user_input_parts)!=3):
                print("Invalid format! Please provide both request peer IP and port.")
                return
            if(not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid format! Please provide both target peer IP and port.")
            else:
                disconnect_peer(user_input_parts[1],int(user_input_parts[2]))
        
        # peer functionality cmds:
        case "/check_tracker_connected":
            check_tracker_connected()
        case "/check_target_peer_connected":# [target_peer_IP]
            if (len(user_input_parts)!=3):
                print("Invalid format! Please provide both request peer IP and port.")
                return
            if(not user_input_parts[1] or not user_input_parts[2]):
                print("Invalid format! Please provide both target peer IP and port.")
            else:
                check_target_peer_connected(user_input_parts[1],user_input_parts[2])
        case "/see_this_peer_info":
            see_this_peer_info()
        case "/see_peer_set":
            see_peer_set()
        case "/see_connected":
            see_connected()
        case "/see_torrent_struct":
            see_torrent_struct()
        case "/see_chunk_status":
            see_chunk_status()
        case "/merge_chunks":
            if (len(user_input_parts)!=2):
                print("Invalid format! Please provide file name.")
                return
            if(not user_input_parts[1]):
                print("Invalid format! Please provide file name.")
            else:
                merge_chunks(user_input_parts[1])
        case _:
            pass

def command_thread():
    while running:
        peer_ip=this_peer_info["ip"]
        peer_port=this_peer_info["listen_port"]
        print(f"[{peer_ip},{peer_port}] ",end='')
        user_input = input()
        command_handler(user_input)
        if(user_input=="/quit_torrent"):
            quit()


if __name__ == "__main__":
    peer_init()
    command_thrd = threading.Thread(target=command_thread)
    command_thrd.start()
    listening_socket.listen()
    while running:
        request_handler_socket,request_peer_addr = listening_socket.accept() # detect a target peer connect
        thread = threading.Thread(target=handle_request_peer_connection,args=(request_handler_socket,request_peer_addr)) # create a "listening peer" thread
        thread.start()
        print(f"[ACTIVE CONNECTION] {threading.active_count()-1}")
    

