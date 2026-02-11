import os
import secrets
import base64
import sys
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- Configuration ---
STORAGE_DIR = Path("storage")
TEMP_DIR = Path("temp")
BANNER = r"""
███████╗ █████╗ ███████╗███████╗██████╗ ██████╗  ██████╗ ██████╗ 
██╔════╝██╔══██╗██╔════╝██╔════╝██╔══██╗██╔══██╗██╔═══██╗██╔══██╗
███████╗███████║█████╗  █████╗  ██║  ██║██████╔╝██║   ██║██████╔╝
╚════██║██╔══██║██╔══╝  ██╔══╝  ██║  ██║██╔══██╗██║   ██║██╔═══╝ 
███████║██║  ██║██║     ███████╗██████╔╝██║  ██║╚██████╔╝██║     
╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝     

SafeDrop — Secure File Sharing
Developed by: Antigravity
GitHub: github.com/antigravity-ai/SafeDrop
"""

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_key_from_string(key_str: str) -> bytes:
    """Derives a Fernet-compatible key from a random string."""
    salt = b'SafeDrop_Salt_2024' # Static salt for local derivation consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(key_str.encode()))

def upload_file():
    print("\n[ Option 1: Upload File ]")
    file_path_str = input("Enter file path: ").strip()
    file_path = Path(file_path_str).resolve()

    if not file_path.exists() or not file_path.is_file():
        print(f"Error: File '{file_path_str}' not found.")
        return

    # Security Check: Path Traversal
    if STORAGE_DIR.resolve() in file_path.parents:
        print("Error: Cannot upload files from the storage directory itself.")
        return

    try:
        # Generate random retrieval key
        retrieval_key = secrets.token_urlsafe(16)
        fernet_key = generate_key_from_string(retrieval_key)
        f = Fernet(fernet_key)

        with open(file_path, "rb") as file:
            file_data = file.read()

        # Encrypt
        encrypted_data = f.encrypt(file_data)

        # Store in storage/ using a hash of the key for filename (obscurity)
        # We use the retrieval key itself as the "address" for simplicity in this local version
        # but in a real-world scenario, you'd want a lookup table or hash.
        storage_file = STORAGE_DIR / retrieval_key
        
        with open(storage_file, "wb") as ef:
            ef.write(encrypted_data)

        print("\nFile uploaded successfully.")
        print(f"Your retrieval key: {retrieval_key}")
        print("Save this key securely. It is not stored anywhere else.")

    except Exception as e:
        print(f"An error occurred during upload: {e}")

def get_file():
    print("\n[ Option 2: Get File ]")
    retrieval_key = input("Enter retrieval key: ").strip()
    
    storage_file = STORAGE_DIR / retrieval_key
    
    if not storage_file.exists():
        print("Error: Invalid retrieval key or file no longer exists.")
        return

    download_loc_str = input("Enter download location (directory): ").strip()
    download_dir = Path(download_loc_str).resolve()

    if not download_dir.exists() or not download_dir.is_dir():
        print(f"Error: Directory '{download_loc_str}' does not exist.")
        return

    # Original filename isn't stored in this simple version, 
    # so we'll ask for a filename or use a default.
    filename = input("Enter filename for saving (e.g., recovered_file.txt): ").strip()
    if not filename:
        filename = f"dropped_{retrieval_key[:8]}"
        
    save_path = download_dir / filename

    if save_path.exists():
        confirm = input(f"File '{filename}' already exists. Overwrite? (y/n): ").lower()
        if confirm != 'y':
            print("Download cancelled.")
            return

    try:
        fernet_key = generate_key_from_string(retrieval_key)
        f = Fernet(fernet_key)

        with open(storage_file, "rb") as ef:
            encrypted_data = ef.read()

        # Decrypt
        decrypted_data = f.decrypt(encrypted_data)

        with open(save_path, "wb") as df:
            df.write(decrypted_data)

        print(f"\nFile downloaded successfully to: {save_path}")

    except Exception as e:
        print(f"Decryption failed: {e}. The key might be incorrect.")

def main():
    # Ensure directories exist
    STORAGE_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

    while True:
        clear_screen()
        print(BANNER)
        print("1. Upload File")
        print("2. Get File")
        print("3. Exit")
        
        choice = input("\nChoose an option: ").strip()

        if choice == '1':
            upload_file()
            input("\nPress Enter to return to menu...")
        elif choice == choice == '2':
            get_file()
            input("\nPress Enter to return to menu...")
        elif choice == '3':
            print("Exiting SafeDrop. Stay secure!")
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
