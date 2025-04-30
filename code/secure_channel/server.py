...
from cryptography.hazmat.primitives.asymmetric import rsa, dh, padding
from cryptography.hazmat.primitives import hashes, serialization, padding as crypto_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from base64 import b64encode, b64decode

...

CHALLENGE_TEXT = f"{challenge_settings.text} - {challenge_settings.flag}"

# Server state
server_state = {
    "rsa_private": None,
    "dh_params": None,
    "dh_private": None,
    "client_rsa_public": None,
    "client_dh_public": None
}

# Initialize RSA keys and DH parameters on startup
server_state["rsa_private"] = rsa.generate_private_key(
    public_exponent=65537,
    key_size=server_settings.rsa_key_size
)

server_state["dh_params"] = dh.generate_parameters(
    generator=2,
    key_size=server_settings.dh_key_size
)

@app.post("/exchange/rsa-dh-params", response_model=RSAandDHParams)
def exchange_rsa_keys(client_key: PublicKey):
    try:
        # Store client's RSA public key
        server_state["client_rsa_public"] = serialization.load_pem_public_key(
            client_key.key.encode()
        )
        
        # Return server's RSA public key and DH parameters
        server_rsa_public = server_state["rsa_private"].public_key()

        return RSAandDHParams(
            key=server_rsa_public.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode(),

            dh_params=server_state["dh_params"].parameter_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.ParameterFormat.PKCS3
            ).decode()
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@app.post("/exchange/dh", response_model=SignedPublicKey)
def exchange_signed_dh_keys(client_key: SignedPublicKey):
    try:
        # 1. Verify client's signature over their DH public key
        ...

        # 2. Store client's DH public key
        ...

        # 3. Generate server's DH key pair
        server_state["dh_private"] = ...
        server_dh_public = ...

        # 4. Prepare server's DH public key in PEM format
        server_dh_public_pem = server_dh_public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # 5. Sign (DH params || server DH public || client DH public)
        signature = server_state["rsa_private"].sign(
            server_state["dh_params"].parameter_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.ParameterFormat.PKCS3
            ) + server_dh_public_pem + client_key.key.encode(),
            padding=padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            algorithm=hashes.SHA256()
        )

        return SignedPublicKey(
            key=server_dh_public_pem.decode(),
            signature=b64encode(signature).decode()
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@app.get("/challenge", response_model=Challenge)
def get_challenge():
    try:
        # 1. Calculate shared DH secret
        shared_secret = ...

        # 2. Derive AES key using HKDF
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"ServerClient",
            info=None
        ).derive(shared_secret)

        # 3. Encrypt challenge with AES-256-CBC using proper padding
        padder = crypto_padding.PKCS7(128).padder()
        padded_data = padder.update(CHALLENGE_TEXT.encode())
        padded_data += padder.finalize()

        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv)
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return Challenge(
            iv=b64encode(iv).decode(),
            ciphertext=b64encode(ciphertext).decode()
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

