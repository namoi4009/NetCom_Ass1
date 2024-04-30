from peer_helper2 import *

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
    

