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
import threading
import requests
from pathlib import Path
import sys
import multiprocessing
from typing import Union

from gui import App, EnvInput
from api import Spotify
from logger import logger
from system_tray import SystemTray

# Author: Sagi Tsafrir
# Github: https://github.com/sagsag00/SpotifyBar
VERSION = "0.2.6"

def is_bigger_version(version: str, compared_version: str) -> bool:
    """Checks if version is bigger or equals to compared_version"""

    v1 = [int(x) for x in version.split(".")]
    v2 = [int(x) for x in compared_version.split(".")]

    return v1 >= v2

def check_new_version() -> bool:
    response = requests.get("https://github.com/sagsag00/SpotifyBar/releases/latest")
    new_version = response.url.split("/")[-1].replace("v", "")
    
    return not is_bigger_version(VERSION, new_version)

def download_new_version() -> None:
    response = requests.get("https://github.com/sagsag00/SpotifyBar/releases/latest")
    new_version = response.url

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    from api.refresh import load_credentials
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent
    
    logger.info("main_thread: Loading program")

    env_file = base_dir / ".env"
    
    if not env_file.exists():
        env_file.write_text("CLIENT_ID=\nCLIENT_SECRET=\nREFRESH_TOKEN=")
        
    creds = load_credentials(env_file)
    CLIENT_ID = creds["CLIENT_ID"]
    CLIENT_SECRET = creds["CLIENT_SECRET"]

    while not (cred := load_credentials(env_file))["CLIENT_ID"] or not cred["CLIENT_SECRET"]:
        window = EnvInput("Input Credentials", None)
        window.run()

    CLIENT_ID = cred["CLIENT_ID"]
    CLIENT_SECRET = cred["CLIENT_SECRET"]
    
    if check_new_version():
        download_new_version()
        exit(0)
    
    spotify = Spotify()
    # if not spotify.open_spotify_app():
    #     logger.critical("main_thread: Couldn't open the spotify app.")
    
    try:
        with open("config.ini", "r") as file:
            logger.info("main_thread: Reading the contents of 'config.ini'")
            lines = file.readlines()
    except FileNotFoundError:
        logger.warning("main_thread: 'config.ini' file was not found. Creating a new file.")
        
        lines = ["program_title=\n",
                 "opacity=\n",
                 "background_color=\n",
                 "buttons_color=\n"
                 "position=\n",
                 "padding=\n",
                 "background_mode=song\n",
                 "soft_color_mode=\n"
                 ]
        
        with open("config.ini", "x") as file:
            file.writelines(lines)
            
        logger.info("main_thread: 'config.ini' created.")
        
    config_values = {}
    for line in lines:
        if '=' in line:
            key, value = line.strip().split('=', 1)
            config_values[key] = value
    
    program_title: str = config_values.get("program_title") or "Spotify Bar"
    position: str = config_values.get("position") or "top_end"
    padding: int = int(config_values.get("padding") or 10)
    opacity: float = float(config_values.get("opacity") or 1)
    background_color: str = config_values.get("background_color") or "lightgray"
    buttons_color: Union[str, None] = str(config_values.get("buttons_color")) or None
    background_mode: str = config_values.get("background_mode") or "default"
    soft_color_mode: bool = str(config_values.get("soft_color_mode") or "true").lower() in ("1", "true", "yes", "on")
        
    app = App(program_title,
              "icon.ico",
              position=position,
              padding=padding,
              opacity=opacity,
              background_color=background_color,
              buttons_color=buttons_color,
              background_mode=background_mode,
              soft_color_mode=soft_color_mode
              )
    tray = SystemTray()
    
    if background_mode == "background_only":
        app.set_background_as_image()
    
    tray_process = threading.Thread(target=tray.run) 

    tray_process.start()
    app.run()