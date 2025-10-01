import socket
import threading
import json
import time

# Configuration
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Arbitrary non-privileged port
MAX_CLIENTS = 10

# Global state to track connected clients and messages
clients = []
client_locks = {} # Lock for each client's send buffer
message_buffer = {} # Stores incoming messages waiting to be polled by clients

def broadcast(sender_sock, message, sender_id):
    """Sends a message to all clients *except* the sender."""
    # The message is simply stored in the buffer of all other clients
    message_data = json.loads(message)
    # Exclude POLL messages from printing server log clutter
    if message_data.get('type') != 'POLL':
        print(f"[SERVER] Received from {sender_id}: {message_data.get('type', 'N/A')}")

    # Add message to all other client buffers
    for client_id, buffer in message_buffer.items():
        if client_id != sender_id:
            with client_locks[client_id]:
                buffer.append(message_data)
                
    # Delay the sender's own buffer update slightly to simulate propagation delay
    # The sender receives an ACK message to prevent their own diff from looping back
    if sender_id in message_buffer and message_data.get('type') != 'POLL':
         with client_locks[sender_id]:
            message_buffer[sender_id].append({"type": "SYNC_ACK", "time": time.time()})

def handle_client(conn, addr, client_id):
    """Handles all communication with a single connected client."""
    print(f"[SERVER] New connection from {addr} (ID: {client_id})")
    
    # Initialize message buffer and lock for this client
    message_buffer[client_id] = []
    client_locks[client_id] = threading.Lock()
    
    try:
        while True:
            # Receive data (Editor Diffs, Process Data, or POLL request)
            data = conn.recv(4096)
            if not data:
                break
            
            messages = data.decode('utf-8').strip().split('\n')
            for message in messages:
                if message:
                    try:
                        message_data = json.loads(message)
                        
                        # 1. Handle POLL request (The client wants to receive messages)
                        if message_data.get('type') == 'POLL':
                            # Respond by sending all queued messages
                            with client_locks[client_id]:
                                if message_buffer[client_id]:
                                    messages_to_send = message_buffer[client_id]
                                    message_buffer[client_id] = [] # Clear buffer after sending
                                    
                                    response_json = json.dumps(messages_to_send) + '\n'
                                    conn.sendall(response_json.encode('utf-8'))
                        
                        # 2. Handle data messages (Editor Diff, Process Data, etc.)
                        else:
                            broadcast(conn, message, client_id)

                    except json.JSONDecodeError:
                        print(f"[SERVER WARNING] Received malformed JSON from {client_id}")
            
    except ConnectionResetError:
        print(f"[SERVER INFO] Client {client_id} reset connection.")
    except Exception as e:
        print(f"[SERVER ERROR] Client {client_id} disconnected unexpectedly: {e}")
    finally:
        print(f"[SERVER] Client {client_id} disconnected.")
        # Clean up global state
        if conn in clients: clients.remove(conn)
        if client_id in message_buffer: del message_buffer[client_id]
        if client_id in client_locks: del client_locks[client_id]
        conn.close()

def main_server():
    """Starts the main server thread."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    s.bind((HOST, PORT))
    s.listen(MAX_CLIENTS)
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    client_counter = 0
    try:
        while True:
            conn, addr = s.accept()
            client_counter += 1
            client_id = f"User-{client_counter}"
            clients.append(conn)
            
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, client_id))
            client_thread.daemon = True 
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        for client in clients:
            try:
                client.close()
            except:
                pass
        s.close()

if __name__ == "__main__":
    main_server()
