import base64
import os
from datetime import datetime, timedelta
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from glom import glom
from jose import JWTError, jwt
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from yaml import load
from yaml.loader import SafeLoader


def get_setting(settings, path, env_var):
    """Get setting from environment variable or fall back to config file."""
    return os.environ.get(env_var, glom(settings, path))


# Load YAML configuration
with open("config.yaml") as f:
    settings = load(f, Loader=SafeLoader)


def encode_flag(flag: str) -> str:
    """Encode flag in base64 to emphasize encoding != encryption"""
    return base64.b64encode(flag.encode()).decode()


class JWTSettings(BaseSettings):
    secret_key: str = get_setting(settings, "lab.arpspoofing.jwt.secret_key", "JWT_SECRET_KEY")
    algorithm: Literal["HS256", "HS512"] = get_setting(
        settings, "lab.arpspoofing.jwt.algorithm", "JWT_ALGORITHM"
    )
    access_token_expire_minutes: int = get_setting(
        settings, "lab.arpspoofing.jwt.access_token_expire_minutes", "JWT_EXPIRE_MINUTES"
    )
    flag: str = get_setting(settings, "lab.arpspoofing.flag", "JWT_FLAG")


class AuthSettings(BaseSettings):
    username: str = get_setting(settings, "lab.arpspoofing.auth.username", "AUTH_USERNAME")
    password: str = get_setting(settings, "lab.arpspoofing.auth.password", "AUTH_PASSWORD")


class ServerSettings(BaseSettings):
    name: str = get_setting(settings, "lab.arpspoofing.server.name", "SERVER_NAME")
    port: int = get_setting(settings, "lab.arpspoofing.server.port", "SERVER_PORT")


# Initialize settings
jwt_settings = JWTSettings()
auth_settings = AuthSettings()
server_settings = ServerSettings()

encoded_flag = encode_flag(jwt_settings.flag)

app = FastAPI(title="Authentication Service")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=jwt_settings.access_token_expire_minutes
    )
    to_encode.update(
        {
            "exp": expire,
            "flag": encoded_flag,  # Using base64 encoded flag
            "hint": "encoded != encrypted",
        }
    )
    return jwt.encode(
        to_encode, jwt_settings.secret_key, algorithm=jwt_settings.algorithm
    )


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if (
        form_data.username == auth_settings.username
        and form_data.password == auth_settings.password
    ):
        access_token = create_access_token(data={"sub": form_data.username})
        return Token(access_token=access_token, token_type="bearer")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        jwt.decode(token, jwt_settings.secret_key, algorithms=[jwt_settings.algorithm])
        return {"message": "You have access to protected resource"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=server_settings.port)