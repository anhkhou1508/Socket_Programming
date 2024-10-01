import socket
import threading

SERVER_HOST = "::1"
SERVER_PORT = 6667

server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
connected_clients = {}
channels = {}

#start server by listening and accept new connection
def start_server():
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on port {SERVER_PORT}")
    while True:
        client_socket, address = server_socket.accept()
        print(f"New connection from {address}")
        #handle commands from clients in a separate thread
        threading.Thread(target=handle_command, args=(client_socket, address)).start()

#handle possible command from clients
def handle_command(client_socket, address):
    nickname = ""
    current_channel = None
    try:
        while True:
            data = client_socket.recv(1024).decode().strip()
            if not data:
                break
            #handle NICK command
            if data.startswith("NICK"):
                new_nickname = data.split()[1]
                if new_nickname in connected_clients:
                    client_socket.sendall("Nickname already in use. Please choose another.\r\n".encode())
                    continue
                nickname = new_nickname
                connected_clients[nickname] = client_socket
                client_socket.sendall(f"Welcome {nickname}! You've been registered.\r\n".encode())

            #handle USER command
            elif data.startswith("USER"):
                client_socket.sendall("User registered successfully.\r\n".encode())

            #handle JOIN command
            elif data.startswith("JOIN"):
                channel = data.split()[1]
                #create channel if if doesnt exist
                if channel not in channels:
                    channels[channel] = []
                #add user to channel if they not already in
                if nickname not in channels[channel]:
                    channels[channel].append(nickname)
                    current_channel = channel
                    for user in channels[channel]:
                        if user != nickname:
                            connected_clients[user].sendall(f"{nickname} has joined {channel}\r\n".encode())
                    client_socket.sendall(f":{nickname} JOIN {current_channel}\r\n".encode())
                    client_socket.sendall(f"You have joined {channel}\r\n".encode())
                    client_socket.sendall(f"{nickname} joined {channel}\r\n".encode())  # Notify the user
                else:
                    client_socket.sendall(f"You are already in {channel}.\r\n".encode())
            else:
                client_socket.sendall("Unknown command!\r\n".encode())

    except socket.error as e:
        print(f"Error handling client {address}: {e}")
    finally:
    #remove user from the connected clients and channels
        if nickname in connected_clients:
            del connected_clients[nickname]
            if current_channel and nickname in channels[current_channel]:
                channels[current_channel].remove(nickname)
                # Notify others in the channel about the user leaving
                for user in channels[current_channel]:
                    connected_clients[user].sendall(f"{nickname} has left {current_channel}\r\n".encode())
        client_socket.close()


def main():
    start_server()

if __name__ == "__main__":
    main()
