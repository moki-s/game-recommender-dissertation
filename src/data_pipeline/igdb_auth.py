"""get a temporary access token so later scripts can call the igdb api."""

import os
import requests

from dotenv import load_dotenv

load_dotenv()

IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")

TOKEN_URL = "https://id.twitch.tv/oauth2/token"


def get_token():
    # asking for a brand new token every time this runs instead of saving one, because igdb tokens expire after a while and a saved one could go stale
    params = {
        "client_id": IGDB_CLIENT_ID,
        "client_secret": IGDB_CLIENT_SECRET,
        "grant_type": "client_credentials",
        # to tell twitch this is a server-to-server request, not a human logging in - slight LLM help
    }

    response = requests.post(TOKEN_URL, params=params)
    # send a post request and not get because we are asking twitch to create a token

    response.raise_for_status()
    # stop here with a clear error if twitch rejected the request

    data = response.json()

    token = data["access_token"]
    # pull out just the token string

    print("received an igdb access token")

    return token
   


if __name__ == "__main__":
    get_token()
