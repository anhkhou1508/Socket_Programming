import socket
import threading

SERVER_HOST = "::1"
SERVER_PORT = 6667
server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

connected_clients = {}
channels = {}
user_details = {}

# Start server by listening and accepting new connections
def start_server():
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on port {SERVER_PORT}")
    
    while True:
        client_socket, address = server_socket.accept()
        print(f"New connection from {address}")
        threading.Thread(target=handle_clients, args=(client_socket, address)).start()

# Handle the clients' connection
def handle_clients(client_socket, address):
    nickname = ""
    current_channel = None
    try:
        while True:
            data = client_socket.recv(1024).decode().strip()
            if not data:
                break
            # If the client sends data, delegate it to handle_command
            nickname, current_channel = handle_command(client_socket, data, nickname, current_channel)
    except socket.error as e:
        print(f"Error handling client {address}: {e}")
    finally:
        if nickname in connected_clients:
            del connected_clients[nickname]
        if current_channel and nickname in channels[current_channel]:
            channels[current_channel].remove(nickname)
            for user in channels[current_channel]:
                connected_clients[user].sendall(f"{nickname} has left {current_channel}\r\n".encode())
        client_socket.close()

# Handle commands from clients
def handle_command(client_socket, data, nickname, current_channel):
    if data.startswith("NICK"):
        new_nickname = data.split()[1]
        if new_nickname in connected_clients:
            client_socket.sendall("Nickname already in use. Please choose another.\r\n".encode())
        else:
            if nickname:
                client_socket.sendall(f"You are now known as {new_nickname}.\r\n".encode())
                del connected_clients[nickname]
            else:
                client_socket.sendall(f"Welcome {new_nickname}! You've been registered.\r\n".encode())
            nickname = new_nickname
            connected_clients[nickname] = client_socket

    elif data.startswith("USER"):
        parts = data.split(" ", 4)
        if len(parts) < 5:
            client_socket.sendall("ERROR: Invalid USER command. Expected format: USER <username> <hostname> <servername> <realname>\r\n".encode())
        else:
            username = parts[1]
            realname = parts[4][1:]  # Remove the leading colon from realname
            user_details[nickname] = {"username": username, "realname": realname}
            client_socket.sendall(f"USER command accepted. Welcome {realname} ({username})!\r\n".encode())

    elif data.startswith("JOIN"):
        if not nickname:
            client_socket.sendall("ERROR: You must set a nickname before joining a channel.\r\n".encode())
        else:
            channel = data.split()[1]
            if channel not in channels:
                channels[channel] = []
            if nickname not in channels[channel]:
                channels[channel].append(nickname)
                current_channel = channel
                # Notify others in the channel that a new user has joined
                for user in channels[channel]:
                    if user != nickname:
                        connected_clients[user].sendall(f"{nickname} has joined {channel}\r\n".encode())
                
                # Send a join message to the user
                client_socket.sendall(f":{nickname} JOIN {current_channel}\r\n".encode())
                client_socket.sendall(f"You have joined {channel}\r\n".encode())
                client_socket.sendall(f"{nickname} joined {channel}\r\n".encode())  # Notify the user
                
                # Send the list of users in the channel to all users in the channel
                user_list = ", ".join(channels[channel])
                for user in channels[channel]:
                    connected_clients[user].sendall(f"Users in {channel}: {user_list}\r\n".encode())
            else:
                client_socket.sendall(f"You are already in {channel}.\r\n".encode())
    else:
        client_socket.sendall("Unknown command!\r\n".encode())
    
    return nickname, current_channel

def main():
    start_server()

if __name__ == "__main__":
    main()
