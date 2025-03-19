from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os
import yaml
from glom import glom

app = FastAPI(title="ECB Deterministic Lab")

def get_setting(settings, path, env_var):
    """Get setting from environment variable or fall back to config file."""
    return os.environ.get(env_var, glom(settings, path))

# Load configuration
with open("config.yaml", "r") as f:
    settings = yaml.safe_load(f)

class ServerSettings(BaseSettings):
    port: int = get_setting(settings, "lab.ecb_deterministic.server.port", "SERVER_PORT")
    flag: str = get_setting(settings, "lab.ecb_deterministic.flag", "FLAG")


server_settings = ServerSettings()

# Generate a random 128-bit key at startup
KEY = os.urandom(16)
cipher = Cipher(algorithms.AES(KEY), modes.ECB())

class Plaintext(BaseModel):
    plaintext: str = Field(description="ASCII/UTF-8 encoded plaintext")

    @validator('plaintext')
    def validate_plaintext(cls, v):
        if not v:
            raise ValueError("Plaintext cannot be empty")
        try:
            v.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError("Invalid UTF-8 input")
        return v

class ChallengeRequest(BaseModel):
    index: int = Field(description="Starting index in the flag")
    length: int = Field(description="Length of the flag portion to encrypt")

    @validator('index')
    def validate_index(cls, v):
        if v < 0:
            raise ValueError("Index must be non-negative")
        return v

    @validator('length')
    def validate_length(cls, v):
        if v <= 0:
            raise ValueError("Length must be positive")
        return v

class Ciphertext(BaseModel):
    ciphertext: str = Field(description="Hex-encoded ciphertext")

def encrypt_data(data: bytes) -> bytes:
    """Helper function to handle padding and encryption"""
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data)
    padded_data += padder.finalize()

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data)
    ciphertext += encryptor.finalize()
    return ciphertext

@app.post("/", response_model=Ciphertext)
def encrypt_plaintext(plaintext: Plaintext):
    try:
        plaintext_bytes = plaintext.plaintext.encode('utf-8')
        ciphertext = encrypt_data(plaintext_bytes)
        return Ciphertext(ciphertext=ciphertext.hex())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/challenge", response_model=Ciphertext)
def encrypt_flag_portion(request: ChallengeRequest):
    try:
        flag_bytes = server_settings.flag.encode('utf-8')
        if request.index >= len(flag_bytes):
            raise ValueError("Index out of range")
            
        # Extract the requested portion of the flag
        flag_portion = flag_bytes[request.index:request.index + request.length]
        if not flag_portion:
            raise ValueError("No data to encrypt (index/length out of bounds)")
            
        ciphertext = encrypt_data(flag_portion)
        return Ciphertext(ciphertext=ciphertext.hex())
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=server_settings.port)