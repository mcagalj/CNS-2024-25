import logging
import os
import time

import requests
import schedule
from glom import glom
from yaml import SafeLoader, load

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_setting(settings, path, env_var):
    """Get setting from environment variable or fall back to config file."""
    return os.environ.get(env_var, glom(settings, path))


# Load YAML configuration
with open("config.yaml") as f:
    settings = load(f, Loader=SafeLoader)

# Get settings with environment variable override
SERVER_NAME = get_setting(settings, "lab.arpspoofing.server.name", "SERVER_NAME")
SERVER_PORT = get_setting(settings, "lab.arpspoofing.server.port", "SERVER_PORT")
USERNAME = get_setting(settings, "lab.arpspoofing.auth.username", "USERNAME")
PASSWORD = get_setting(settings, "lab.arpspoofing.auth.password", "PASSWORD")


def authenticate():
    try:
        response = requests.post(
            f"http://{SERVER_NAME}:{SERVER_PORT}/token",
            data={"username": USERNAME, "password": PASSWORD},
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            logger.info(f"Successfully authenticated! Token: {token}")

            # Try accessing protected route
            protected_response = requests.get(
                f"http://{SERVER_NAME}:{SERVER_PORT}/protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            logger.info(f"Protected route response: {protected_response.json()}")
        else:
            logger.error(f"Authentication failed: {response.text}")
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}")


def main():
    logger.info("Starting authentication client...")

    # Schedule authentication every 30 seconds
    schedule.every(30).seconds.do(authenticate)

    # Run authentication immediately on startup
    authenticate()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()