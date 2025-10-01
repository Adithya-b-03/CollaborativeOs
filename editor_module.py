import os
import time
import difflib

# --- Configuration ---
SHARED_FILE = "shared_document.txt"

# --- INTERFACE FUNCTIONS FOR MEMBER 1 (NETWORKING) ---

# TODO: Member 1 MUST implement these functions in their networking module
# and you MUST import and use them here.

def send_diff_to_network(diffs: list):
    """
    Placeholder for Core Task 3: Synchronization Logic (Sending).
    
    YOU will call this function when local changes are detected.
    Member 1 will implement the logic to serialize the 'diffs' list and
    broadcast it to all other connected clients.
    """
    if diffs:
        # Simulate Network send delay
        time.sleep(0.1) 
        print(f"[NETWORK] Sending {len(diffs)} diffs to peers...")
    return True # Simulate success

def poll_remote_updates():
    """
    Placeholder for Core Task 4: Real-Time Updates (Receiving).
    
    YOU will call this function frequently.
    Member 1 will implement the logic to check their incoming message queue
    and return any new 'diffs' received from other users.
    
    For now, we return a hardcoded simulated remote update.
    """
    # Simulate receiving remote updates only once every 5 seconds
    if int(time.time()) % 5 == 0:
        print("[NETWORK] Detected incoming remote update.")
        return [{
            "type": "replace",
            "line_start_old": 3,
            "line_end_old": 4,
            "line_start_new": 3,
            "line_end_new": 4,
            "text": ["A remote user just added this line via the network!"]
        }]
    return [] # Return empty list if no updates

# --- Core Task 1: Initial Setup ---
def load_document():
    """
    Loads the content of the shared document or creates it if it doesn't exist.
    Returns: A tuple (current_content, last_synced_content)
    """
    if not os.path.exists(SHARED_FILE):
        print(f"Creating new shared document: {SHARED_FILE}")
        with open(SHARED_FILE, 'w') as f:
            f.write("Welcome to the Collaborative OS Editor!\n\n")
            f.write("Start typing here and press 'S' to sync.")

    with open(SHARED_FILE, 'r') as f:
        content = f.read().splitlines()
    
    return content, content[:]

def display_editor(content):
    """
    Displays the current content of the document with line numbers.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 50)
    print(f"COLLABORATIVE EDITOR (Editing: {SHARED_FILE})")
    print("-" * 50)
    for i, line in enumerate(content):
        print(f"{i+1:02d}: {line}")
    print("-" * 50)
    print("Commands: [L <line_num> <new_text>] | [Q]uit | [S]ync")
    print("STATUS: Waiting for input...")

def get_user_edit(current_content):
    """
    Simulates user editing a single line of the document.
    
    Returns: A tuple (success_flag, updated_content)
    """
    command = input("Edit (e.g., L 3 New content here): ").strip()
    
    if command.upper() == 'Q':
        return False, current_content
    
    if command.upper() == 'S':
        print(">>> Checking for local changes...")
        return True, current_content
        
    try:
        if command.upper().startswith('L '):
            parts = command.split(' ', 2)
            line_num = int(parts[1])
            new_text = parts[2]
            
            if 1 <= line_num <= len(current_content):
                updated_content = current_content[:]
                updated_content[line_num - 1] = new_text
                return True, updated_content
            else:
                print("Invalid line number.")
                return True, current_content
        else:
            print("Invalid command. Use L <line_num> <text>.")
            return True, current_content

    except (IndexError, ValueError):
        print("Error in command format. Use L <line_num> <text>.")
        return True, current_content

# --- Core Task 2: Change Tracking ---
def calculate_diff(old_content, new_content):
    """
    Compares old content to new content and generates a list of changes (a "diff").
    """
    diffs = []
    differ = difflib.SequenceMatcher(None, old_content, new_content)
    
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            continue
        
        diff_item = {
            "type": tag,  # 'replace', 'delete', 'insert'
            "line_start_old": i1 + 1,
            "line_end_old": i2,
            "line_start_new": j1 + 1,
            "line_end_new": j2,
            "text": new_content[j1:j2] # The new text for the change
        }
        diffs.append(diff_item)

    return diffs

# --- Core Task 4: Real-Time Updates (Applying) ---
def apply_diffs(current_content, diffs):
    """
    Applies a list of received changes (a "diff") to the local content.
    Returns the updated content.
    """
    updated_content = current_content[:]
    
    # NOTE: The apply logic must be in reverse order (e.g., from the end of the file
    # backwards) to ensure line numbers remain accurate if multiple inserts/deletes happen.
    # However, for simplicity using 'difflib' output, we rely on its structure for now.
    
    for diff in diffs:
        diff_type = diff['type']
        
        if diff_type == 'replace':
            start_index = diff['line_start_old'] - 1
            end_index = diff['line_end_old']
            updated_content[start_index:end_index] = diff['text']
            
        elif diff_type == 'delete':
            start_index = diff['line_start_old'] - 1
            end_index = diff['line_end_old']
            del updated_content[start_index:end_index]
            
        elif diff_type == 'insert':
            # Insert at the specified new start line
            start_index = diff['line_start_new'] - 1
            updated_content[start_index:start_index] = diff['text']
            
    return updated_content

def run_editor_cli():
    """Main loop for the CLI editor."""
    current_content, last_synced_content = load_document()
    running = True
    
    while running:
        display_editor(current_content)
        
        # 1. Handle user input
        success, new_content = get_user_edit(current_content)
        
        if not success:
            running = False
            continue
            
        # 2. Check for local changes and calculate diff
        diffs = calculate_diff(last_synced_content, new_content)
        
        if diffs:
            print(f"\n[LOCAL CHANGE] Detected {len(diffs)} change(s).")
            
            # --- CORE TASK 3: SENDING THE CHANGE ---
            send_diff_to_network(diffs) 
            
            # Update synced state immediately after 'sending'
            last_synced_content = new_content[:]
            current_content = new_content
            
            # Save the physical file to reflect the change
            with open(SHARED_FILE, 'w') as f:
                f.write('\n'.join(current_content))
            print("[SYNC SUCCESS] Local change recorded and sent.")
        else:
            print("\n[INFO] No local changes to sync.")
            current_content = new_content # Update content even if no sync was needed

        # 3. Handle receiving remote updates
        remote_diffs = poll_remote_updates()
        
        if remote_diffs:
            print(f"[REMOTE UPDATE] Received {len(remote_diffs)} update(s). Applying...")
            
            # --- CONFLICT RESOLUTION (Implicit in the application order) ---
            # If a local edit (step 2) and remote edit (step 3) happen simultaneously,
            # the local edit is sent first, and then the remote edit is applied
            # on top of it. This is a basic "last-write-wins" resolution strategy.
            current_content = apply_diffs(current_content, remote_diffs)
            
            # Update the synced state to the new, merged content
            last_synced_content = current_content[:] 
            
            # Save the physical file
            with open(SHARED_FILE, 'w') as f:
                f.write('\n'.join(current_content))
            print("[MERGE COMPLETE] Remote updates applied.")
            
        # Pause briefly before looping to prevent rapid display refresh
        time.sleep(0.5)

if __name__ == "__main__":
    run_editor_cli()
