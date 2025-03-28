import logging
import os
import time
from base64 import b64encode

import requests
from requests.exceptions import ConnectionError
import yaml
from glom import glom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_setting(settings, path, env_var):
    """Get setting from environment variable or fall back to config file."""
    return os.environ.get(env_var, glom(settings, path))

# Load YAML configuration
with open("config.yaml") as f:
    settings = yaml.safe_load(f)

# Get settings with environment variable override
SERVER_NAME = get_setting(settings, "lab.low_entropy.server.name", "SERVER_NAME")
SERVER_PORT = get_setting(settings, "lab.low_entropy.server.port", "SERVER_PORT")
USERNAME = get_setting(settings, "lab.low_entropy.auth.username", "USERNAME")
PASSWORD = get_setting(settings, "lab.low_entropy.auth.password", "PASSWORD")

def get_basic_auth_header():
    """Generate Basic Auth header"""
    credentials = b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}

def authenticate(session):
    """Authenticate and get a new session"""
    try:
        # Login to get the session cookie
        response = session.post(
            f"http://{SERVER_NAME}:{SERVER_PORT}/login",
            headers=get_basic_auth_header()
        )
        
        if response.status_code == 200:
            logger.info("Successfully authenticated!")
            if 'session_id' in session.cookies:
                logger.info(f"Received session cookie: {session.cookies['session_id']}")
            return True
        else:
            logger.error(f"Authentication failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}")
        return False

def access_protected(session):
    """Try to access the protected route"""
    try:
        protected_response = session.get(
            f"http://{SERVER_NAME}:{SERVER_PORT}/protected"
        )
        
        if protected_response.status_code == 200:
            logger.info(f"Protected route response: {protected_response.json()}")
            return True
        else:
            logger.error(f"Failed to access protected route: {protected_response.text}")
            return False
    except Exception as e:
        logger.error(f"Error accessing protected route: {str(e)}")
        return False

def wait_for_server(session, retry_delay=2):
    """Wait indefinitely for server to become available"""
    while True:
        try:
            response = session.get(f"http://{SERVER_NAME}:{SERVER_PORT}/")
            if response.status_code == 404:
                return True
            return True
        except ConnectionError:
            logger.info(f"Server not ready, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error while waiting for server: {str(e)}")
            time.sleep(retry_delay)

def main():
    logger.info("Starting authentication client...")
    
    with requests.Session() as session:
        wait_for_server(session)

        while True:
            if authenticate(session):
                break
            logger.info("Authentication failed, retrying in 2 seconds...")
            time.sleep(2)

        while True:
            time.sleep(30)
            
            if not access_protected(session):
                logger.info("Session might have expired, re-authenticating...")
                while True:
                    if authenticate(session):
                        break
                    logger.info("Re-authentication failed, retrying in 2 seconds...")
                    time.sleep(2)

if __name__ == "__main__":
    main()