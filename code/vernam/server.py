from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import yaml
import hmac
import hashlib
import os
from glom import glom

app = FastAPI(title="Vernam Cipher Lab")

def get_setting(settings, path, env_var):
    """Get setting from environment variable or fall back to config file."""
    return os.environ.get(env_var, glom(settings, path))

# Load configuration
with open("config.yaml", "r") as f:
    settings = yaml.safe_load(f)

class ServerSettings(BaseSettings):
    port: int = get_setting(settings, "lab.vernam.server.port", "SERVER_PORT")

class VernamSettings(BaseSettings):
    key_seed: str = get_setting(settings, "lab.vernam.key_seed", "VERNAM_KEY_SEED")
    key_size: int = get_setting(settings, "lab.vernam.key_size", "VERNAM_KEY_SIZE")
    challenge_text: str = get_setting(settings, "lab.vernam.challenge_text", "VERNAM_CHALLENGE_TEXT")
    flag: str = get_setting(settings, "lab.vernam.flag", "VERNAM_FLAG")

# Initialize settings
server_settings = ServerSettings()
vernam_settings = VernamSettings()

class Plaintext(BaseModel):
    plaintext: str = Field(description="Hex-encoded plaintext (e.g. '414141' for 'AAA')")

    @validator('plaintext')
    def validate_plaintext(cls, v):
        if not v:
            raise ValueError("Plaintext cannot be empty. Example: '414141' for 'AAA'")
        try:
            bytes.fromhex(v)
        except ValueError:
            raise ValueError("Invalid hex input. Example: '414141' for 'AAA'")
        return v

class Ciphertext(BaseModel):
    ciphertext: str = Field(description="Hex-encoded ciphertext")

def derive_key(key_seed: str, key_length: int) -> bytes:
    return hmac.new(
        key_seed.encode('ascii'),
        b"vernam-cipher",
        hashlib.sha256
    ).digest()[:key_length]

def xor_cipher(key: bytes, message: bytes) -> bytes:
    # Calculate how many complete key blocks we need
    complete_blocks = len(message) // len(key)
    remainder_size = len(message) % len(key)
    
    # Generate keystream for complete blocks
    keystream = key * complete_blocks
    
    # Add remaining bytes from the beginning of the key if needed
    if remainder_size > 0:
        keystream += key[:remainder_size]
        
    return bytes(k ^ m for k, m in zip(keystream, message))

# Derive the key once at startup
KEY = derive_key(key_seed=vernam_settings.key_seed, key_length=vernam_settings.key_size)

# Create challenge ciphertext ensuring ASCII encoding
challenge_text = f"{vernam_settings.challenge_text} - {vernam_settings.flag}"
CHALLENGE = challenge_text.encode('ascii')
CHALLENGE_CIPHERTEXT = xor_cipher(KEY, CHALLENGE)

@app.post("/", response_model=Ciphertext)
def encrypt_plaintext(plaintext: Plaintext):
    try:
        plaintext_bytes = bytes.fromhex(plaintext.plaintext)
        ciphertext = xor_cipher(KEY, plaintext_bytes)
        return Ciphertext(ciphertext=ciphertext.hex())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.get("/challenge", response_model=Ciphertext)
def get_challenge():
    return Ciphertext(ciphertext=CHALLENGE_CIPHERTEXT.hex())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=server_settings.port)