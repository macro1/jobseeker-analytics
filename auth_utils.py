import logging
import os
import uuid

from constants import SCOPES, CLIENT_SECRETS_FILE, REDIRECT_URI, GOOGLE_CLIENT_ID
from file_utils import get_user_filepath

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2 import id_token

logger = logging.getLogger(__name__)

class AuthenticatedUser:
    """
    The AuthenticatedUser class is used to 
    store information about the user. This
    class is instantiated after the user has
    successfully authenticated with Google.
    """
    def __init__(self, creds: Credentials):
        self.creds = creds
        self.user_id = self.get_user_id()
        self.filepath = get_user_filepath(self.user_id)

    def get_user_id(self) -> str:
        """
        Retrieves the user ID from Google OAuth2 credentials.

        Parameters:

        Returns:
        - user_id: The unique user ID.
        """
        try:
            logger.info("Verifying ID token...")
            decoded_token = id_token.verify_oauth2_token(self.creds.id_token, Request(), audience=GOOGLE_CLIENT_ID)
            user_id = decoded_token['sub']  # 'sub' is the unique user ID
            return user_id
        except (KeyError, TypeError):
            self.creds = self.creds.refresh(Request())
            if not self.creds.id_token:
                proxy_user_id = str(uuid.uuid4())
                logger.error("Could not retrieve user ID. Using proxy ID: %s", proxy_user_id)
                return proxy_user_id # Generate a random ID
            if not hasattr(self, '_retry'):
                self._retry = True
                return self.get_user_id()
            else:
                proxy_user_id = str(uuid.uuid4())
                logger.error("Could not retrieve user ID after retry. Using proxy ID: %s", proxy_user_id)
                return proxy_user_id
        except Exception as e:
            logger.error("Error verifying ID token: %s", e)
            proxy_user_id = str(uuid.uuid4())
            logger.error("Could not verify ID token. Using proxy ID: %s", proxy_user_id)
            return proxy_user_id # Generate a random ID


def get_user() -> AuthenticatedUser:
    """Handles the OAuth2 flow and retrieves user credentials."""
    creds = None
    logger.info("Checking for existing credentials...")

    # Try to load existing credentials from token.json
    if os.path.exists('token.json'):
        logger.info("Loading existing credentials...")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if not creds.valid:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
            # Save refreshed credentials for the next run
            with open('token.json', 'w', encoding='utf-8') as token_file:
                logger.info("Saving credentials...")
                token_file.write(creds.to_json())
        else:
            logger.info("No valid credentials found. Redirecting to authorization URL...")
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES, 
                redirect_uri=REDIRECT_URI
            )
            authorization_url, state = flow.authorization_url(prompt="consent")
            logger.info("Authorization URL: %s", authorization_url)
            logger.info("State: %s", state)
            return authorization_url  # Return the authorization URL for user to visit

    return AuthenticatedUser(creds)
