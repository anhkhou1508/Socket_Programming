
import socket
import time


SERVER_HOST = "::1"
SERVER_PORT = 6667
NICKNAME = "Superbot"
channel = "#test"
bot_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
def connect_to_server():
    try:
        bot_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"{NICKNAME} connected to the server at {SERVER_HOST}:{SERVER_PORT}")
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        bot_socket.close()
def identify_to_server():
    try:
        bot_socket.sendall(f"NICK {NICKNAME}\r\n".encode())
        bot_socket.sendall(f"USER {NICKNAME} 0 * :{NICKNAME}\r\n".encode())
        print(f"{NICKNAME} have already identified to the server")
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        bot_socket.close()

def send_private_message(target, message):
    try:
        bot_socket.sendall(f"PRIVMSG {target} :{message}\r\n".encode())
    except socket.error as e:
        print(f"Error sending message: {e}")
        bot_socket.close()
def keep_connection_alive():
    try:
        while True:
            imcoming_message = bot_socket.recv(1024).decode()
            print(f"Received message: {imcoming_message}")
            if imcoming_message.startswith("PING"):
                bot_socket.sendall(f"PONG {imcoming_message.split()[1]}\r\n".encode())
                print("sent PONG to server")
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        bot_socket.close()

def join_channel():
    try:
        bot_socket.sendall(f"JOIN {channel}\r\n".encode())
        send_private_message(channel, "Hi, im a bot")
        print(f"{NICKNAME} has joined {channel}")
    except socket.error as e:
        print(f"Error joining channel: {e}")
        bot_socket.close()


def main():
    connect_to_server()
    identify_to_server()
    time.sleep(1)
    join_channel()
    keep_connection_alive()

if __name__ == "__main__":
    main()




