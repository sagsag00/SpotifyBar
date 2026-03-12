# Copyright 2024 Sagi Tsafrir

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import base64
import json
import urllib.parse
from flask import Flask, request
import webbrowser
import dotenv
import os
from pathlib import Path
from werkzeug.serving import run_simple
import time
import threading
import signal
import sys
from multiprocessing import Process

if getattr(sys, "frozen", False):
    base_dir = Path(sys.executable).resolve().parent
else:
    base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))  
from logger import logger

env_file = base_dir / ".env"    
app = Flask(__name__)

def load_credentials(env_path: Path):
    """Load credentials from the given .env file."""
    dotenv.load_dotenv(env_path, override=True)
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")

    return {
        "CLIENT_ID": client_id,
        "CLIENT_SECRET": client_secret,
        "REFRESH_TOKEN": refresh_token
    }

class SpotifyAuth:
    def __init__(self, client_id, client_secret):
        """Spotify authorization."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = "http://127.0.0.1:5000/callback"  # The servers url.
        self.server_process = None
        self.auth_complete = threading.Event()
    

    def get_authorization_url(self) -> str:
        """Makes the url for the authorization.
        
        Returns:
            str: auth_url. The authorization url.
        """
        scope = "ugc-image-upload user-read-playback-state user-modify-playback-state user-read-currently-playing app-remote-control streaming playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-follow-modify user-follow-read user-read-playback-position user-top-read user-read-recently-played user-library-modify user-library-read user-read-email user-read-private"
        encoded_redirect_uri = urllib.parse.quote(self.redirect_uri)

        auth_url = f"https://accounts.spotify.com/authorize?client_id={self.client_id}&response_type=code&redirect_uri={encoded_redirect_uri}&scope={scope}"
        return auth_url

    def exchange_code_for_token(self, code: str) -> tuple[None, None] | tuple[str, str]:
        """Gets access_token and refresh_token using the client code.

        Args:
            code (str): Client code. Able to get only using the authorization url with a website.

        Returns:
            tuple[str, str]: (access_token, refresh_token).
        """
        url = "https://accounts.spotify.com/api/token"
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(url, headers=headers, data=data)
        self.handle_response(response)

        if response.status_code != 200:
            return None, None
        
        return response.json().get('access_token'), response.json().get("refresh_token")

    def refresh(self, refresh_token: str) -> str:
        """Refreshes the access_token using the refresh_token.

        Args:
            refresh_token (str).

        Returns:
            str: access_token.
        """
        url = "https://accounts.spotify.com/api/token"
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        response = requests.post(url, headers=headers, data=data)
        self.handle_response(response)

        if response.status_code != 200:
            return None

        return response.json().get("access_token")

    def handle_response(self, response: requests.Response) -> None:
        """Handle responses to check for errors and output response data for debugging."""
        try:
            response_data = response.json()
            if response.status_code != 200:
                logger.error(f"SpotifyAuth.handle_response: Error {response.status_code}: {response_data}")
        except json.JSONDecodeError:
            logger.error(f"SpotifyAuth.handle_response: Response not in JSON format: {response.text}")

    def run(self) -> str:  
        creds = load_credentials(env_file)
        if not creds["REFRESH_TOKEN"]:
            auth_url = self.get_authorization_url()
            webbrowser.open(auth_url)
            
            self.server_process = Process(target=run_server)
            self.server_process.start()
            
            while True:
                time.sleep(0.5)
                creds = load_credentials(env_file)

                if creds["REFRESH_TOKEN"]:
                    break
            
            if self.server_process.is_alive():
                self.server_process.terminate()
                self.server_process.join()
        return creds["REFRESH_TOKEN"]
   
   
def run_server():
    run_simple("127.0.0.1", 5000, app, threaded=True)  
         
def save_refresh_token():
    code = request.args.get('code')
    creds = load_credentials(env_file)
    CLIENT_ID = creds["CLIENT_ID"]
    CLIENT_SECRET = creds["CLIENT_SECRET"]
    REFRESH_TOKEN = creds["REFRESH_TOKEN"]
    spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET)
    if not code:
        return
    access_token, refresh_token = spotify_auth.exchange_code_for_token(code)
    if refresh_token:
        save_to_env("REFRESH_TOKEN", refresh_token)
    
    if access_token:
        logger.info(f"refresh.callback: Access Token: {access_token}")
        logger.info(f"refresh.callback: Refresh Token: {refresh_token}")

        new_access_token = spotify_auth.refresh(refresh_token)
        if new_access_token:
            logger.info(f"refresh.callback: New Access Token: {new_access_token}")
            
@app.route('/callback')
def callback():
    """The website that handles the redirect from the authorization url."""
    save_refresh_token()
    return "Authorization complete. You can close this window."

def save_to_env(name: str, value: str) -> None:
    """Saves the given name with the given value to the .env file.

    Args:
        name (str): The name of the environment variable.
        value (str): The value of the environment variable.
    """
    if getattr(sys, 'frozen', False): 
        base_dir = Path(sys.executable).resolve().parents[0]  
    else:
        base_dir = Path(__file__).resolve().parents[1] 
        
    logger.debug(f"{base_dir=}")
        
    env_file = base_dir / ".env"
    
    lines = []
    if env_file.exists():
        with open(env_file, "r") as file:
            lines = file.readlines()
            
    variable_exists = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{name}="):
            lines[i] = f"{name}={value}\n"
            variable_exists = True
            break
    if not variable_exists:
        lines.append(f"{name}={value}\n")
        
    with open(env_file, "w") as file:
        file.writelines(lines)

if __name__ == "__main__":
    creds = load_credentials(env_file)
    CLIENT_ID = creds["CLIENT_ID"]
    CLIENT_SECRET = creds["CLIENT_SECRET"]
    REFRESH_TOKEN = creds["REFRESH_TOKEN"]
    spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET)
    
    if not REFRESH_TOKEN:
        auth_url = spotify_auth.get_authorization_url()
        webbrowser.open(auth_url)
        app.run("127.0.0.1", 5000)
    else:
        new_access_token = spotify_auth.refresh(REFRESH_TOKEN)
        if new_access_token:
            logger.info(f"refresh: {new_access_token=}")
        else:
            logger.error("refresh: Failed to refresh access token.")
    
