import os
import pickle
from cryptography.fernet import Fernet

class YounezGPTKeys:
    def __init__(self):
        self.keys = {}
        self.current_key = None
        self.key_file = "keys.bin"
        self.key_encrypter = None

        # Load existing keys from file or create new file
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                self.keys = pickle.load(f)
        else:
            with open(self.key_file, "wb") as f:
                pickle.dump(self.keys, f)

        # Create encrypter for key file
        self.create_encrypter()

    def add_key(self, name, key):
        # Add new key to dictionary
        self.keys[name] = key

        # Save keys to file
        with open(self.key_file, "wb") as f:
            pickle.dump(self.keys, f)

    def remove_key(self, name):
        # Remove key from dictionary
        if name in self.keys.keys():
            del self.keys[name]

        # Save keys to file
        with open(self.key_file, "wb") as f:
            pickle.dump(self.keys, f)

    def set_current_key(self, name):
        # Set current key based on name
        if name in self.keys.keys():
            self.current_key = self.keys[name]

    def get_current_key(self):
        # Return current key
        return self.current_key

    def get_key_names(self):
        # Return list of key names
        return list(self.keys.keys())

    def create_encrypter(self):
        # Create encrypter for key file
        key = Fernet.generate_key()
        self.key_encrypter = Fernet(key)

        # Load keys from file
        with open(self.key_file, "rb") as f:
            keys_bytes = f.read()

        # Encrypt keys and save to file
        encrypted_keys = self.key_encrypter.encrypt(keys_bytes)
        with open(self.key_file, "wb") as f:
            f.write(encrypted_keys)

    def load_keys(self, key):
        # Decrypt keys from file
        with open(self.key_file, "rb") as f:
            encrypted_keys = f.read()

        keys_bytes = self.key_encrypter.decrypt(encrypted_keys)
        self.keys = pickle.loads(keys_bytes)

        # Set current key to first key in dictionary
        if len(self.keys.keys()) > 0:
            self.current_key = list(self.keys.keys())[0]
        else:
            self.current_key = None

        # Save decrypted keys to file
        self.save_keys(key)

    def save_keys(self, key):
        # Save keys to file
        with open(self.key_file, "wb") as f:
            pickle.dump(self.keys, f)

        # Encrypt keys and save to file
        with open(self.key_file, "rb") as f:
            keys_bytes = f.read()

        encrypted_keys = self.key_encrypter.encrypt(keys_bytes)
        with open(self.key_file, "wb") as f:
            f.write(encrypted_keys)

        # Set current key to None
        self.current_key = None

        # Set new encrypter for key file
        self.create_encrypter()

