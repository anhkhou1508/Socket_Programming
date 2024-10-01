import socket
import random
import time
import threading



class IRC_bot:
    def __init__(self, SERVER_HOST="::1", SERVER_PORT=6667, NICKNAME="SuperBot", CHANNEL="#test"):
        self.SERVER_HOST = SERVER_HOST
        self.SERVER_PORT = SERVER_PORT
        self.NICKNAME = NICKNAME
        self.CHANNEL = CHANNEL
        self.bot_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.active_users = []
        self.temporary_channels = {}
        self.fun_facts = [
            "Random facts: Octopus has 3 hearts",
            "Joke: Parallel lines have so much in common. Its a shame they will never meet",
            "VietNam has an S-shape"
        ]

    def get_information(self):
        while True:
            try:
                print("Enter commands prefixed with '--':")
                server_host = input("|host| to enter server host: ")
                if server_host.startswith("--host"):
                    self.SERVER_HOST = server_host.split()[1]
                    break
                else:
                    print("Invalid input. Please use the format: --host <hostname>")
            except IndexError:
                print("Error: Please provide a host address after '--host'")
        
        while True:
            try:
                server_port = input("|port| to enter your server port: ")
                if server_port.startswith("--port"):
                    self.SERVER_PORT = int(server_port.split()[1])
                    if 1 <= self.SERVER_PORT <= 65535:  # Validating port range
                        break
                    else:
                        print("Error: Port number must be between 1 and 65535.")
                else:
                    print("Invalid input. Please use the format: --port <port_number>")
            except (IndexError, ValueError):
                print("Error: Please provide a valid port number after '--port'.")

        while True:
            try:
                nickname = input("|name| to enter your bot's name: ")
                if nickname.startswith("--name"):
                    self.NICKNAME = nickname.split()[1]
                    break
                else:
                    print("Invalid input. Please use the format: --name <nickname>")
            except IndexError:
                print("Error: Please provide a nickname after '--name'.")

        while True:
            try:
                channel = input("|channel| (space) |#channel| to enter channel: ")
                if channel.startswith("--channel"):
                    self.CHANNEL = channel.split()[1]
                    if not self.CHANNEL.startswith("#"):  # Channel name validation
                        print("Error: Channel name must start with '#'.")
                    else:
                        break
                else:
                    print("Invalid input. Please use the format: --channel <#channel>")
            except IndexError:
                print("Error: Please provide a channel name after '--channel'.")



            
    # Connect to server through address host and port of the server
    def connect_to_server(self):
        try:
            self.bot_socket.connect((self.SERVER_HOST, self.SERVER_PORT))
            print(f"{self.NICKNAME} connected to the server at {self.SERVER_HOST}:{self.SERVER_PORT}")
        except socket.error as e:
            print(f"Error connecting to server: {e}")
            self.bot_socket.close()

    # Identify to the server by sending NICK and USER command to server
    def identify_to_server(self):
        try:
            self.bot_socket.sendall(f"NICK {self.NICKNAME}\r\n".encode())
            self.bot_socket.sendall(f"USER {self.NICKNAME} 0 * :{self.NICKNAME}\r\n".encode())
            print(f"{self.NICKNAME} has identified to the server")
        except socket.error as e:
            print(f"Error identifying to server: {e}")
            self.bot_socket.close()

    # Send private message by sending PRIVMSG command to server
    def send_message(self, target, message):
        try:
            self.bot_socket.sendall(f"PRIVMSG {target} :{message}\r\n".encode())
        except socket.error as e:
            print(f"Error sending message: {e}")
            self.bot_socket.close()

    def keep_connection_alive(self):
        try:
            while True:
                incoming_message = self.bot_socket.recv(1024).decode()
                print(f"Received message: {incoming_message}")
                
                # Handle PING from server
                if incoming_message.startswith("PING"):
                    self.bot_socket.sendall(f"PONG {incoming_message.split()[1]}\r\n".encode())
                    print("Sent PONG to server")
                    
                
                
                # Handle private messages to the bot
                if "PRIVMSG" in incoming_message and f"PRIVMSG {self.NICKNAME}" in incoming_message:
                    random_fact = random.choice(self.fun_facts)
                    sender_nickname = incoming_message.split('!')[0][1:]  # Extract sender nickname
                    self.send_message(sender_nickname, random_fact)
                    print(f"Sent random fact to {sender_nickname}")
                
                # Handle channel messages
                if "PRIVMSG" in incoming_message and f"PRIVMSG {self.CHANNEL}" in incoming_message:
                    received_message = incoming_message.split(f"PRIVMSG {self.CHANNEL} :")
                    self.handle_command(received_message)
                
                
                # Handle RPL_NAMEREPLY (353) message to capture initial user list
                if "353" in incoming_message:
                    user_list = incoming_message.split(":")[2].strip().split()
                    self.active_users.extend(user_list)
                    print(f"Initial users in channel: {", ".join(self.active_users)}")
                    
                self.update_active_users(incoming_message)

        except socket.error as e:
            print(f"Error keeping connection alive: {e}")
            self.bot_socket.close()

    def handle_command(self, received_message):
        command = received_message[1].strip()  # Get the command part
        if command == "!hello":
            self.send_message(self.CHANNEL, f"Hi everyone! I'm {self.NICKNAME}. What can I help you with today?")
        elif command.startswith("!slap"):
            parts = command.split()
            if len(parts) > 1:
                target = parts[1]
                if target in self.active_users:
                    self.send_message(self.CHANNEL, f"{self.NICKNAME} has slapped {target}!")
                else:
                    self.send_message(self.CHANNEL, f"{target} is not here to be slapped!")
            else:
                self.send_message(self.CHANNEL, f"{self.NICKNAME} has slapped someone!")
        elif command.startswith("!tempchannel"):
            parts = command.split()
            if len(parts) > 1:
                temp_channel_name = f"#{parts[1].lstrip('#')}"  
                self.create_temp_channel(temp_channel_name)
            else:
                self.send_message(self.CHANNEL, "Usage: !tempchannel <channel_name>")
        else:
            self.send_message(self.CHANNEL, "Unknown command")
            
            
            
    def create_temp_channel(self, channel_name):
        if channel_name in self.temporary_channels:
            self.send_message(self.CHANNEL, f"Channel {channel_name} already exists!")
            return

        self.temporary_channels[channel_name] = True
        self.bot_socket.sendall(f"JOIN {channel_name}\r\n".encode())
        self.send_message(self.CHANNEL, f"Temporary channel {channel_name} created! It will expire in 15 seconds.")
        threading.Thread(target=self.expire_temp_channel, args=(channel_name,)).start()

    def expire_temp_channel(self, channel_name):
        time.sleep(15)  # Wait for 15 seconds
        if channel_name in self.temporary_channels:
            del self.temporary_channels[channel_name]
            self.send_message(self.CHANNEL, f"Temporary channel {channel_name} has expired!")
            print(f"Temporary channel {channel_name} has expired.")
            
            
    # Update the active users list based on server messages
    def update_active_users(self, message):
        if "JOIN" in message:
            user_nickname = message.split('!')[0][1:]  
            if user_nickname not in self.active_users and user_nickname != self.NICKNAME:
                self.active_users.append(user_nickname)
                print(f"User joined: {user_nickname}")

        elif "PART" in message or "QUIT" in message:
            user_nickname = message.split('!')[0][1:]  
            if user_nickname in self.active_users:
                self.active_users.remove(user_nickname)
                print(f"User left: {user_nickname}")
                


    # Join a channel by sending JOIN command to server
    def join_channel(self):
        try:
            self.bot_socket.sendall(f"JOIN {self.CHANNEL}\r\n".encode())
            self.send_message(self.CHANNEL, "Hi, I'm a bot")
            print(f"{self.NICKNAME} has joined {self.CHANNEL}")
        except socket.error as e:
            print(f"Error joining channel: {e}")
            self.bot_socket.close()


def main():
    # Create an instance of IRC_bot
    bot = IRC_bot()

    # Call methods using the bot instance
    bot.get_information()
    bot.connect_to_server()
    bot.identify_to_server()
    time.sleep(1)
    bot.join_channel()
    bot.keep_connection_alive()


if __name__ == "__main__":
    main()
