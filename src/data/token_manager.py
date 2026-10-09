import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

"""
File name: token_manager.py
Recommended token manager function from Open Sky to generate new tokens.
"""

load_dotenv()
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# How many seconds before expiry to proactively refresh the token.
TOKEN_REFRESH_MARGIN = 30

def token_refresh():
    """Fetch a new access token from the OpenSky authentication server."""

    class TokenManager:
        def __init__(self):
            self.token = None
            self.expires_at = None

        def get_token(self):
            """Return a valid access token, refreshing automatically if needed."""
            if self.token and self.expires_at and datetime.now() < self.expires_at:
                return self.token
            return self._refresh()

        def _refresh(self):
            """Fetch a new access token from the OpenSky authentication server."""
            r = requests.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                },
            )
            r.raise_for_status()

            data = r.json()
            self.token = data["access_token"]
            expires_in = data.get("expires_in", 1800)
            self.expires_at = datetime.now() + timedelta(seconds=expires_in - TOKEN_REFRESH_MARGIN)
            return self.token

        def headers(self):
            """Return request headers with a valid Bearer token."""
            return {"Authorization": f"Bearer {self.get_token()}"}


    # Create a single shared instance for your script.
    tokens = TokenManager()

    return tokens.headers()