import socket
import threading

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