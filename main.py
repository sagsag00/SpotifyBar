import views.buttons
import views.label
import views.scales
import gui_manager
from gui import App
from api import Spotify
from logger import logger
from system_tray import SystemTray
import threading

# Author: Sagi Tsafrir
# Github: https://github.com/sagsag00/SpotifyBar

#TODO Make it so that if the player is paused, the check for playback change thread will be destroyed.
if __name__ == "__main__":
    spotify = Spotify()
    if not spotify.open_spotify_app():
        logger.critical("main_thread: Couldn't open the spotify app.")
    
    try:
        with open("config.ini", "r") as file:
            logger.info("main_thread: Reading the contents of 'config.ini'")
            lines = file.readlines()
    except FileNotFoundError:
        logger.warning("main_thread: 'config.ini' file was not found. Creating a new file.")
        
        # Create default lines if the file does not exist
        lines = ["program_title=\n", "opacity=\n", "background_color=\n", "position=\n", "padding=\n"]
        
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

    app = App(program_title, "icon.ico", position=position, padding=padding, opacity=opacity, background_color=background_color)
    tray = SystemTray()
    
    tray_process = threading.Thread(target=tray.run) 
    
    tray_process.start()
    app.run()