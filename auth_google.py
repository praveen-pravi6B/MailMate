import os
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv, set_key

# Load existing .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be in your .env file.")
    exit(1)

# Scopes needed
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_refresh_token():
    print("Generating client config...")
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    print("Starting OAuth flow. Your browser will open.")
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    
    if creds and creds.refresh_token:
        print("\nSuccess! We got the refresh token.")
        set_key(env_path, "GMAIL_REFRESH_TOKEN", creds.refresh_token)
        print("I have automatically saved GMAIL_REFRESH_TOKEN into your .env file!")
    else:
        print("\nFailed to get a refresh token. Make sure you don't already have an active session, or try clearing app permissions in your Google account.")

if __name__ == '__main__':
    get_refresh_token()
