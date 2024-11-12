import views.buttons
import views.label
import views.scales
import gui_manager
from gui import App
from api import Spotify
from logger import logger

if __name__ == "__main__":
    
    spotify = Spotify()
    if not spotify.open_spotify_app():
        logger.critical("main_thread: Couldn't open the spotify app.")
        # raise Exception("Couldn't open spotify app.")
    
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
    program_title: str = config_values.get("program_title", "Spotify Bar") or "Spotify Bar"
    position: str = config_values.get("position", "bottom_start") or "bottom_start"
    padding: int = int(config_values.get("padding", 10) or 10)
    opacity: float = float(config_values.get("opacity", 1) or 1)
    background_color: str = config_values.get("background_color", "lightgray") or "lightgray"

    app = App(program_title, "icon.ico", position=position, padding=padding, opacity=opacity, background_color=background_color)
    app.run()
    
    #TODO maybe decrypt the .env file.