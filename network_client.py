import socket
import json
import time
import uuid

# Configuration
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 4096

# Global state
client_socket = None
# Generate a consistent, unique ID for this client instance
CLIENT_ID = str(uuid.uuid4())[:8] 
is_connected = False

def initialize_client():
    """Initializes and connects the client socket to the server."""
    global client_socket, is_connected
    if is_connected:
        return True

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[NETWORK] Attempting connection to {HOST}:{PORT} (ID: {CLIENT_ID})...")
        client_socket.connect((HOST, PORT))
        is_connected = True
        print(f"[NETWORK] Connected successfully.")
        return True
    except ConnectionRefusedError:
        print(f"[NETWORK ERROR] Connection refused. Is the server running?")
        return False
    except Exception as e:
        print(f"[NETWORK ERROR] Failed to connect: {e}")
        return False

def send_message(message_type: str, data: dict):
    """Sends a structured message (e.g., Editor Diff or Process Data) to the server."""
    if not is_connected and not initialize_client():
        return False
        
    try:
        full_message = {
            "source_id": CLIENT_ID,
            "type": message_type,
            "timestamp": time.time(),
            "data": data
        }
        
        json_message = json.dumps(full_message) + '\n'
        client_socket.sendall(json_message.encode('utf-8'))
        return True
    except Exception as e:
        print(f"[NETWORK ERROR] Failed to send message: {e}")
        global is_connected
        is_connected = False
        return False

def poll_messages():
    """Checks for and retrieves any waiting messages (updates) from the server."""
    if not is_connected and not initialize_client():
        return []
        
    try:
        # 1. Send POLL request to trigger the server's response
        poll_msg = json.dumps({"type": "POLL", "source_id": CLIENT_ID}) + '\n'
        client_socket.sendall(poll_msg.encode('utf-8'))
        
        # 2. Receive the response (will contain all buffered messages)
        client_socket.settimeout(0.1) 
        response_data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        client_socket.settimeout(None) 
        
        if response_data:
            # Response is expected to be a JSON array of messages
            messages = json.loads(response_data.strip())
            return messages
        
        return []

    except socket.timeout:
        return []
    except Exception as e:
        print(f"[NETWORK ERROR] Failed to poll messages: {e}")
        global is_connected
        is_connected = False
        return []
