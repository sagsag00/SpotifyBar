import requests
import base64
import json
import urllib.parse
from flask import Flask, request
import webbrowser
import dotenv
import os
from pathlib import Path
from logger import logger
from werkzeug.serving import run_simple
import time
import threading
import signal
import sys

dotenv.load_dotenv()
app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")


class SpotifyAuth:
    """Spotify authorization.
    """
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = "http://localhost:5000/callback"  # The servers url.
    

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
        """Handle responses to check for errors and output response data for debugging.
        """
        try:
            response_data = response.json()
            if response.status_code != 200:
                logger.error(f"SpotifyAuth.handle_response: Error {response.status_code}: {response_data}")
        except json.JSONDecodeError:
            logger.error(f"SpotifyAuth.handle_response: Response not in JSON format: {response.text}")

    def run(self) -> None:  
        if not REFRESH_TOKEN:
            auth_url = self.get_authorization_url()
            webbrowser.open(auth_url)
            # app.run("localhost", 5000)
            run_simple("localhost", 5000, app, threaded=True)
            
def shutdown_server():
    time.sleep(5)  # Sleep for 5 seconds before shutting down
    logger.info("Shutting the server down")
    pid = os.getpid()  # Get the current process ID
    os.kill(pid, signal.SIGINT) 
  
@app.route('/shutdown', methods=['POST'])
def shutdown():
    logger.info("Shutdown signal received")
    threading.Thread(target=shutdown_server).start()  # Start background task
    return 'Server shutting down...', 200 

# Flask route to handle the redirect
@app.route('/callback')
def callback():
    """The website that handles the redirect from the authorization url.
    """
    code = request.args.get('code')
    spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET)
    
    if code:
        access_token, refresh_token = spotify_auth.exchange_code_for_token(code)
        logger.critical(f"{refresh_token=}", f"{REFRESH_TOKEN=}")
        if refresh_token:
            save_to_env("REFRESH_TOKEN", refresh_token)
        
        if access_token:
            logger.info(f"refresh.callback: Access Token: {access_token}")
            logger.info(f"refresh.callback: Refresh Token: {refresh_token}")

            new_access_token = spotify_auth.refresh(refresh_token)
            if new_access_token:
                logger.info(f"refresh.callback: New Access Token: {new_access_token}")
             
        threading.Thread(target=shutdown_server).start()  
        
    return "Authorization complete. You can close this window."

def save_to_env(name: str, value: str) -> None:
    """Saves the given name with the given value to the .env file.

    Args:
        name (str): The name of the environment variable.
        value (str): The value of the environment variable.
    """
    if getattr(sys, 'frozen', False):  # Check if running as an executable
        base_dir = Path(sys.executable).resolve().parents[0]  # Frozen app bundle directory
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
    spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET)
    
    if not REFRESH_TOKEN:
        auth_url = spotify_auth.get_authorization_url()
        webbrowser.open(auth_url)
        app.run("localhost", 5000)
    else:
        new_access_token = spotify_auth.refresh(REFRESH_TOKEN)
        if new_access_token:
            logger.info(f"refresh: {new_access_token=}")
        else:
            logger.error("refresh: Failed to refresh access token.")
    
