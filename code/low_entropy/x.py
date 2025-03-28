import os
import logging
from pathlib import Path
import secrets
import base64
...
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

...

SCRYPT_N = 2**16
SCRYPT_R = 8
SCRYPT_P = 1
KEY_LENGTH = 16  # AES-128

def derive_key(student_name: str, entropy_bits: int) -> bytes:
    """Derive encryption key with specified entropy."""
    if entropy_bits < 1:
        raise ValueError("entropy_bits must be at least 1")

    value_bytes = secrets.randbits(entropy_bits).to_bytes((entropy_bits + 7) // 8, "big")    
    
    return Scrypt(
        salt=student_name.encode(), length=KEY_LENGTH, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P
    ).derive(value_bytes)


def encrypt_flag(flag: str, key: bytes, algorithm: str) -> tuple[bytes, bytes]:
    """Encrypt the flag using the specified algorithm."""
    iv = os.urandom(16)
    if algorithm == "aes-128-ctr":
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
        encryptor = cipher.encryptor()
        ct = encryptor.update(flag.encode()) + encryptor.finalize()
    else:  # Default to aes-128-cbc
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(flag.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
    return ct, iv

def write_challenge_file(ciphertext: bytes, iv: bytes) -> None:    
    with open("challenge", "w") as f:
        f.write(base64.b64encode(iv).decode("ascii") + "\n")
        f.write(base64.b64encode(ciphertext).decode("ascii") + "\n")

def main():
    try:
        ...
        
        key = derive_key(config["student_name"], config["key_entropy_bits"])
        ciphertext, iv = encrypt_flag(config["flag"], key, config["encryption_algorithm"])
        write_challenge_file(ciphertext, iv)

    except Exception as e:
        logger.error(f"Failed to setup challenge: {e}")
        raise

if __name__ == "__main__":
    main()