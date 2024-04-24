import socket
import threading
import json
import hashlib

MAX_REQUEST_QUEUE = 20
SERVER_HOST = "192.168.1.137"
SERVER_PORT = 65432

BUFFER_SIZE = 1024

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(BUFFER_SIZE).decode()
            if message:
                print("\nReceived: " + message)
        except:
            print("Error receiving message.")
            break
        
def create_metainfo(files, tracker_url):
    metainfo = {'announce': tracker_url, 'info': {'files': []}}
    for file_name, file_data in files.items():
        file_info = {
            'path': file_name,
            'length': len(file_data),
            'piece_length': 1024,  # Assuming a fixed piece size for simplicity
            'pieces': [hashlib.sha256(file_data[i:i+1024]).hexdigest() for i in range(0, len(file_data), 1024)]
        }
        metainfo['info']['files'].append(file_info)

    with open('metainfo.json', 'w') as outfile:
        json.dump(metainfo, outfile)
                
def generate_magnet_link(file_name, file_hash, tracker_url):
    magnet_link = f"magnet:?xt=urn:btih:{file_hash}&dn={file_name}&tr={tracker_url}"
    return magnet_link

# Client would need to request pieces based on the metainfo
def request_piece(piece_index):
    # Request a specific piece from the server
    pass

def assemble_file(pieces):
    # Combine pieces into the final file
    pass

def main():
    nickname = input("Choose your nickname: ")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("Connected to the chat server!")

        # Start the receiving thread
        thread = threading.Thread(target=receive_messages, args=(client_socket,))
        thread.start()

        while True:
            message = input(f"{nickname}: ")
            if message.lower() == 'exit':
                break
            try:
                client_socket.sendall(f"{nickname}: {message}".encode())
            except:
                print("Disconnecting...")   
                break
                
        client_socket.close()
    
if __name__ == "__main__":
    main()