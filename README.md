#  Simple Like-Torren Application

This is a simple Like-Torrent application built with Python.

## Getting Started

To run this application, you'll need Python installed on your system. 

1. Clone this repository
2. Open with YOUR CODE EDITOR or TERMINAL in the project directory
3. Connect your computer to the internet
4. Change the SERVER_IP in the source code into your device IP
5. Run `python server.py` and `python client.py`
   (Step 3 will run the _server_ and the first client - client1)
6. Open two other terminal and change the directory into `./client2` and `./client3`
7. Run `python client.py` in both two above terminal

## Connect to server and other client

All client has server properties, too. This will allow peer-to-peer connection and tranfer files from client-to-client.
To do this run the command `connect_client [client's IP] [client's PORT]`.
In this project, we already set that client3 automatically connect to two other clients (1) (2).

## Transfer files (Simulation)

For simulation, client1 contains odd-number chunks part (1, 3, 5, 7, 9, 11) and client2 contains the even ones (2, 4, 6, 8, 10, 12).
Run this command `request_download mv1.mp4` in client3 directory. 
If successfull, the chunks will be automatically merge into the original files.

## Other commands
`disconnect_server`: to disconnect to server
`disconnect_client [client IP] [client PORT]`: to disconnect to the specific client
`see_torrent_struct`: to see the torrent file structure (content)
`see_chunk_status`:  to see the status of the chunks (0: not downloaded yet, 1: already downloaded) 
`quit_torrent`: to quit the torrent application

## Caution!!

If you quit the application, it may running in the background and block the ports which allocate for the server and the client(1)(2)(3)
To handle it, please run `netstat -aon | findstr :<port_number>` (server_port: 6789, client_port: 9011, 9021, 9031,...)
If the system file a process that holding that port, please kill that process by running `taskkill /PID <PID number> -f` (with the PID number from the _netstat_ result)

## License

This project belongs to Namoi4009.
