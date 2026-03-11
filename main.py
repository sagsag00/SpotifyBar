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

from gui import App, EnvInput
from api import Spotify
from logger import logger
from system_tray import SystemTray

#TODO When pressing next the background doesn't chagne, and even after a while, it won't refresh
#TODO When starting the app, do the EnvInput, the submit doesn't work yet
# Author: Sagi Tsafrir
# Github: https://github.com/sagsag00/SpotifyBar

VERSION = "0.2.1"

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
    logger.info("main_thread: Loading program")
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
        
        # Create default lines if the file does not exist
        lines = ["program_title=\n",
                 "opacity=\n",
                 "background_color=\n",
                 "position=\n",
                 "padding=\n",
                 "background_mode=default\n",
                 "soft_color_mode=\n"
                 ]
        
        with open("config.ini", "x") as file:
            file.writelines(lines)
            
        logger.info("main_thread: 'config.ini' created.")
        
    # Create a dictionary to store the configuration values
    config_values = {}
    for line in lines:
        # Split each line at the '=' sign to separate keys and values
        if '=' in line:
            key, value = line.strip().split('=', 1)
            config_values[key] = value
    
    # Assign values from config_values dictionary
    # the or is in the cases of it being empty string "" or None.
    program_title: str = config_values.get("program_title") or "Spotify Bar"
    position: str = config_values.get("position") or "bottom_start"
    padding: int = int(config_values.get("padding") or 10)
    opacity: float = float(config_values.get("opacity") or 1)
    background_color: str = config_values.get("background_color") or "lightgray"
    background_mode: str = config_values.get("background_mode") or "default" 
    soft_color_mode: str = bool(config_values.get("soft_color_mode")) or True
    
    app = App(program_title,
              "icon.ico",
              position=position,
              padding=padding,
              opacity=opacity,
              background_color=background_color,
              background_mode=background_mode,
              soft_color_mode=soft_color_mode
              )
    tray = SystemTray()
    
    if background_mode == "background_only":
        app.set_background_as_image()
    
    tray_process = threading.Thread(target=tray.run) 

    tray_process.start()
    app.run()