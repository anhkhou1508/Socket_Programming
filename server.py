import socket
import threading
import time

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
                connected_clients[user].sendall(f":{nickname} QUIT :Leaving\r\n".encode())
        client_socket.close()

# Handle commands from clients
def handle_command(client_socket, data, nickname, current_channel):
    if data.startswith("PING"):
        client_socket.sendall(f":{SERVER_HOST} PONG {SERVER_HOST} :".encode())
    if data.startswith("NICK"):
        new_nickname = data.split()[1]
        if new_nickname in connected_clients:
            client_socket.sendall(f":{SERVER_HOST} 433 {nickname} {new_nickname} :Nickname already in use.\r\n".encode())  # ERR_NICKNAMEINUSE (433)
        else:
            if nickname:
                client_socket.sendall(f":{SERVER_HOST} 001 {new_nickname} :You are now known as {new_nickname}.\r\n".encode())
                del connected_clients[nickname]
            else:
                client_socket.sendall(f":{SERVER_HOST} 001 {new_nickname} :Welcome to the IRC network, {new_nickname}!\r\n".encode())
                client_socket.sendall(f":{SERVER_HOST} 002 {new_nickname} :Your host is {SERVER_HOST}, running version 1.0\r\n".encode())  # RPL_YOURHOST
                client_socket.sendall(f":{SERVER_HOST} 003 {new_nickname} :This server was created {time.ctime()}\r\n".encode())  # RPL_CREATED
                client_socket.sendall(f":{SERVER_HOST} 004 {new_nickname} {SERVER_HOST} 1.0 iowgh\r\n".encode())  # RPL_MYINFO

            nickname = new_nickname
            connected_clients[nickname] = client_socket

    elif data.startswith("USER"):
        parts = data.split(" ", 4)
        if len(parts) < 5:
            client_socket.sendall(f":{SERVER_HOST} 461 {nickname} :Not enough parameters\r\n".encode())  
        else:
            username = parts[1]
            realname = parts[4][1:]  
            user_details[nickname] = {"username": username, "realname": realname}
            client_socket.sendall(f":{SERVER_HOST} 001 {nickname} :USER command accepted. Welcome {realname} ({username})!\r\n".encode())

    elif data.startswith("JOIN"):
        if not nickname:
            client_socket.sendall(f":{SERVER_HOST} 451 :You have not registered\r\n".encode())
        else:
            channel = data.split()[1]
            if channel.startswith("0"):
                #Notify leaving on current channel
                if current_channel: 
                    if nickname in channels[current_channel]:
                        channels[current_channel].remove(nickname)
                        for user in channels[current_channel]:
                            connected_clients[user].sendall(f":{nickname} PART {current_channel} :Leaving\r\n".encode())
                            send_message_tochannel(current_channel, f"You have left channel {current_channel}.")
                        client_socket.sendall(f":{nickname} PART {current_channel} :Leaving.\r\n".encode())
                
                # Notify leaving on previouse connected channel
                for previouse_channel in list(channels.keys()):
                    if nickname in channels[previouse_channel]:
                        channels[previouse_channel].remove(nickname)
                        send_message_tochannel(previouse_channel, f"You have left channel {previouse_channel}.")
                        client_socket.sendall(f":{nickname} PART {previouse_channel} :Leaving\r\n".encode())
                current_channel = None
                return nickname, current_channel
            
            elif channel.startswith("#"):
                if channel not in channels:
                    channels[channel] = []
                if nickname not in channels[channel]:
                    channels[channel].append(nickname)
                    current_channel = channel
                    for user in channels[channel]:
                        if user != nickname:
                            connected_clients[user].sendall(f":{nickname} JOIN {channel}\r\n".encode())
                    client_socket.sendall(f":{nickname} JOIN {current_channel}\r\n".encode())
                    user_list = " ".join(channels[channel])
                    client_socket.sendall(f":{SERVER_HOST} 353 {nickname} = {channel} :{user_list}\r\n".encode()) 
                    client_socket.sendall(f":{SERVER_HOST} 366 {nickname} {channel} :End of /NAMES list.\r\n".encode())  
                    send_message_tochannel(channel, f"Users in channel {channel}: {user_list}")
                else: 
                    client_socket.sendall(f":{SERVER_HOST} 443 {nickname} {channel} :You're already in the channel\r\n".encode()) 
            else:
                client_socket.sendall(f":{SERVER_HOST} 403 {nickname} {channel} :No such channel\r\n".encode())
    else:
        client_socket.sendall(f":{SERVER_HOST} 421 {nickname} {data.split()[0]} :Unknown command\r\n".encode()) 
    return nickname, current_channel                
                
                

def send_message_tochannel(channel, message):
    if channel in channels:
        for user in channels[channel]:
            connected_clients[user].sendall(f":{SERVER_HOST} PRIVMSG {channel} :{message}\r\n".encode())



def main():
    start_server()

if __name__ == "__main__":
    main()
