import logging
from logging.handlers import RotatingFileHandler
import paramiko
import threading
import socket
import time
from pathlib import Path
from datetime import datetime


# Constants for configuration
class Config:
    SSH_BANNER = "SSH-2.0-MySSHServer_1.0 hello mother fucker !! "
    BASE_DIR = Path(__file__).parent.parent
    SERVER_KEY = BASE_DIR / 'Honeypot' / 'server.key'
    CREDS_LOG_FILE = BASE_DIR / 'Honeypot' / 'creds_audits.log'
    CMD_LOG_FILE = BASE_DIR / 'Honeypot' / 'cmd_audits.log'
    SSH_PORT = 2224
    MAX_CONN = 100
    USERNAME = 'username'
    PASSWORD = 'password'
    TARPIT = False



# Initialize logging
def setup_logger(log_file, max_bytes=2000, backup_count=5):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


# Setup main loggers
funnel_logger = setup_logger(Config.CMD_LOG_FILE)
creds_logger = setup_logger(Config.CREDS_LOG_FILE)


# SSH Server Class
class SSHServer(paramiko.ServerInterface):
    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        return "password"

    def check_auth_password(self, username, password):
        funnel_logger.info(f'Client {self.client_ip} attempted login with username: {username}, password: {password}')
        creds_logger.info(f'{self.client_ip}, {username}, {password}')
        if self.input_username and self.input_password:
            if username == self.input_username and password == self.input_password:
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        return True


# Emulated shell to simulate commands
def emulated_shell(channel, client_ip):
    channel.send(b"BERNICHI_Emulated_Shell$ ")
    command = b""

    # Fake file system and directory structure
    file_system = {
        'jumpbox1.conf': 'Go to deeboodah.com\r\n',
        'readme.txt': 'This is a test file with some random content.\r\n',
    }

    directories = {
        '/': ['jumpbox1.conf', 'readme.txt'],
        '/home': [],
    }

    current_dir = '/'

    while True:
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()

        command += char
        if char == b"\r":
            if command.strip() == b'exit':
                channel.send(b"\n Goodbye!\n")
                channel.close()
            elif command.strip() == b'pwd':
                # Print the current working directory
                channel.send(f"\n{current_dir}\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'whoami':
                channel.send(b"\ncorporate-jumpbox-user\r\n")
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'ls':
                # List files in the current directory
                files = directories.get(current_dir, [])
                file_list = '\r\n'.join(files) if files else 'No files found'
                channel.send(f"\n{file_list}\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'cat jumpbox1.conf':
                channel.send(file_system.get('jumpbox1.conf', b'File not found\r\n'))
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'cat readme.txt':
                channel.send(file_system.get('readme.txt', b'File not found\r\n'))
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'date':
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                channel.send(f"\n{current_time}\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'-h' or command.strip() == b'help':
                help_text = (
                    "\nAvailable commands:\n"
                    "  exit     - Close the connection.\n"
                    "  pwd      - Show the current directory.\n"
                    "  whoami   - Show the current user.\n"
                    "  ls       - List directory contents.\n"
                    "  cat      - Show the contents of a file.\n"
                    "  date     - Show current date and time.\n"
                    "  mkdir    - Create a new directory.\n"
                    "  rm       - Remove a file.\n"
                    "  touch    - Create a new file.\n"
                    "  echo     - Echo text to the terminal.\n"
                    "  help     - Show this help message.\n"
                )
                channel.send(help_text.encode())
                funnel_logger.info(f'Help requested by {client_ip}')
            elif command.strip().startswith(b'mkdir'):
                dir_name = command.strip().split(b' ')[1]
                if dir_name not in directories:
                    directories[dir_name.decode()] = []
                    channel.send(f"\nDirectory '{dir_name.decode()}' created\r\n".encode())
                else:
                    channel.send(f"\nDirectory '{dir_name.decode()}' already exists\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip().startswith(b'rm'):
                file_name = command.strip().split(b' ')[1]
                if file_name in file_system:
                    del file_system[file_name]
                    channel.send(f"\nFile '{file_name.decode()}' removed\r\n".encode())
                else:
                    channel.send(f"\nFile '{file_name.decode()}' not found\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip().startswith(b'touch'):
                file_name = command.strip().split(b' ')[1]
                if file_name not in file_system:
                    file_system[file_name] = ''
                    directories[current_dir].append(file_name.decode())
                    channel.send(f"\nFile '{file_name.decode()}' created\r\n".encode())
                else:
                    channel.send(f"\nFile '{file_name.decode()}' already exists\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip().startswith(b'echo'):
                text = b' '.join(command.strip().split(b' ')[1:])
                channel.send(f"\n{text.decode()}\r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            else:
                channel.send(f"\n{command.strip().decode()} \r\n".encode())
                funnel_logger.info(f'Command {command.strip()} executed by {client_ip}')
            channel.send(b"corporate-jumpbox2$ ")
            command = b""


# Handle client connections
def handle_client(client, addr, username, password, tarpit=False):
    print(f"Connection received from {addr}")
    client_ip = addr[0]
    print(f"{client_ip} connected to server.")
    try:
        transport = paramiko.Transport(client)
        transport.local_version = Config.SSH_BANNER
        server = SSHServer(client_ip=client_ip, input_username=username, input_password=password)
        transport.add_server_key(paramiko.RSAKey(filename=Config.SERVER_KEY))
        transport.start_server(server=server)

        channel = transport.accept(100)
        if channel is None:
            print("No channel was opened.")
            return

        banner = "Welcome to my game 22.04 LTS (BERNICHI HIHI)!\r\n\r\n"
        if tarpit:
            endless_banner = banner * 100
            for char in endless_banner:
                channel.send(char)
                time.sleep(8)
        else:
            channel.send(banner)

        emulated_shell(channel, client_ip)


    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            transport.close()
        except Exception:
            pass
        client.close()


# Start honeypot server
def start_honeypot(address, port, username, password, tarpit=False):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((address, port))
    server_socket.listen(Config.MAX_CONN)
    print(f"SSH server is listening on port {port}.")

    while True:
        try:
            client, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(client, addr, username, password, tarpit)).start()
        except Exception as error:
            print(f"Could not open new client connection: {error}")


# Run the honeypot
if __name__ == "__main__":
    print("Starting honeypot on 127.0.0.1:2224...")
    start_honeypot('127.0.0.1', Config.SSH_PORT, Config.USERNAME, Config.PASSWORD, tarpit=Config.TARPIT)
