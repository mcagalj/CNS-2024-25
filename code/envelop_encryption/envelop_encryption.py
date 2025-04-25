...
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

...

def encrypt_document(document: bytes, public_key: rsa.RSAPublicKey) -> Tuple[bytes, bytes, bytes, bytes]:
    """Encrypt document using envelope encryption."""
    # Generate AES key and IV
    aes_key = os.urandom(32)  # AES-256
    iv = os.urandom(16)

    # Encrypt document with AES in CTR mode
    cipher = Cipher(algorithms.AES(aes_key), modes.CTR(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(document) + encryptor.finalize()

    # Encrypt AES key with RSA
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return encrypted_aes_key, iv, ciphertext

def write_challenge_files(private_key: rsa.RSAPrivateKey, encrypted_aes_key: bytes, 
                         iv: bytes, ciphertext: bytes, student_home: str) -> None:
    """Write challenge files."""
    challenge_dir = Path(student_home)
    challenge_dir.mkdir(exist_ok=True)

    # Extract RSA parameters
    private_numbers = private_key.private_numbers()
    public_numbers = private_key.public_key().public_numbers()

    # Write challenge data
    with open(challenge_dir / "challenge.txt", "w") as f:
        f.write(f"n = {hex(public_numbers.n)}\n")
        f.write(f"e = {hex(public_numbers.e)}\n")
        f.write(f"p = {hex(private_numbers.p)}  # One prime factor provided\n\n")
        f.write("encrypted_aes_key = ")
        f.write(base64.b64encode(encrypted_aes_key).decode())
        f.write("\n\niv = ")
        f.write(base64.b64encode(iv).decode())
        f.write("\n\nciphertext = ")
        f.write(base64.b64encode(ciphertext).decode())

...

def main():
    try:        
        student_home = f"/home/{config['student_name']}"
        
        # Generate keys and prepare document
        private_key, public_key = generate_rsa_keypair()
        document = create_realistic_document(config["flag"])
        
        # Encrypt document
        encrypted_aes_key, iv, ciphertext = encrypt_document(document, public_key)
        
        # Write challenge files
        write_challenge_files(private_key, encrypted_aes_key, iv, ciphertext, student_home)
        
        
    except Exception as e:
        logger.error(f"Failed to setup challenge: {e}")
        raise

if __name__ == "__main__":
    main()