import logging
import os
import pickle
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "client_secrets.json"


def get_authenticated_service():
    """
    Authenticate and return a YouTube API service object.
    Handles token refresh and re-authentication flow.

    Returns:
        googleapiclient.discovery.Resource: Authenticated YouTube API service

    Raises:
        SystemExit: If authentication fails completely
    """
    creds = None

    # Load existing token if it exists
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
            logger.debug(f"Loaded existing credentials from {TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"Failed to load token file: {e}")
            creds = None

    # If there are no valid credentials, refresh or get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired token...")
                creds.refresh(Request())
                logger.info("Token refreshed successfully")
            except RefreshError as e:
                logger.error(f"Token refresh failed: {e}")
                logger.info("Starting new authentication flow...")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Credentials file {CREDENTIALS_FILE} not found")
                logger.error(
                    "Please download your OAuth2 credentials from Google Cloud Console"
                )
                logger.error("and save them as 'client_secrets.json'")
                raise SystemExit(1)

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Authentication completed successfully")
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                raise SystemExit(1)

        # Save the credentials for the next run
        try:
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
            logger.debug(f"Credentials saved to {TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")

    try:
        service = build("youtube", "v3", credentials=creds)
        logger.debug("YouTube API service created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to build YouTube API service: {e}")
        raise SystemExit(1)


def test_authentication():
    """
    Test authentication by making a simple API call.
    Used for validation in auth.py when run directly.
    """
    try:
        service = get_authenticated_service()
        response = service.channels().list(part="snippet", mine=True).execute()

        if "items" in response and response["items"]:
            channel = response["items"][0]["snippet"]
            print(f"✅ Authentication successful!")
            print(f"Authenticated as: {channel['title']}")
            return True
        else:
            print("❌ Authentication failed: No channel data returned")
            return False

    except SystemExit:
        return False
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("Testing YouTube API authentication...")
    success = test_authentication()
    exit(0 if success else 1)
