import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
...
from fastapi import FastAPI
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import SessionDB

...

app = FastAPI(title="Session Management Service")
security = HTTPBasic()
db = SessionDB()

...

def generate_session_id() -> str:
    """Generate a weak session ID with student-specific salt."""
    entropy_bits = server_settings.session_entropy_bits

    # Generate an integer with the exact entropy bits and convert to bytes
    value_bytes = secrets.randbits(entropy_bits).to_bytes((entropy_bits + 7) // 8, "big")
    
    # Concatenate with student name as salt
    salted = value_bytes + server_settings.student_name.encode()

    # Hash and encode in URL-safe Base64
    hashed = hashlib.sha256(salted).digest()
    return base64.urlsafe_b64encode(hashed).decode('ascii').rstrip('=')

...

@app.get("/protected")
async def protected_route(request: Request) -> dict:
    # Check rate limit first
    rate_limit_key = get_rate_limit_key(request)
    if rate_limiter.is_rate_limited(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    session_id = request.cookies.get("session_id")
        
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session cookie provided"
        )
        
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
        
    if session["expires_at"] < datetime.now(timezone.utc):
        await db.delete_session(session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
        
    return {
        "message": "Access granted",
        "credentials": {
            "username": server_settings.student_name,
            "password": server_settings.target_ssh_pass,
            "hint": server_settings.hint
        },
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=server_settings.port)