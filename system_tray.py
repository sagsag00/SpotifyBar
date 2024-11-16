import os
import signal
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from logger import logger
from gui_manager import GuiManager
import threading

class SystemTray:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        # Making the class singleton.
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SystemTray, cls).__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initializes the system tray menu."""
        if hasattr(self, "initialized"):
            return
        
        # Initializing the system tray menu.
        self.initialized = True
        self.tray = Icon("media_controls")
        self.tray.icon = self.create_image()
        self.tray.menu = Menu(
            MenuItem("Play/Pause", self.play_pause),
            MenuItem("Next", self.next_track),
            MenuItem("Previous", self.previous_track),
            MenuItem("Exit", self.exit_app)
        )
        self.tray.title = "Spotify Bar"
        
        # Initializing the gui manager as a class member, when created in the `gui.py` code, it will be initialized here.
        # See gui.py: App.__create_buttons method for more info.
        self.gui_manager: GuiManager = None

    def play_pause(self) -> None:
        """Play/Pause system tray tab."""
        logger.info("SystemTray.play_pause: Play/Pause clicked") 
        
        if self.gui_manager is None:
            logger.warning("SystemTray.play_pause: GUI is not set yet. Please wait a few moments until the GUI is up.")
            return
        
        threading.Thread(target=self.gui_manager.change_pause_state).start()
        
    def next_track(self) -> None:
        """Next track system tray tab"""
        logger.info("SystemTray.next_track: Next track clicked")
        
        if self.gui_manager is None:
            logger.warning("SystemTray.play_pause: GUI is not set yet. Please wait a few moments until the GUI is up.")
            return
        self.gui_manager.skip_count = 1
        if not self.gui_manager.pause_button.is_active:
            self.gui_manager.pause_button.is_active = True
        
        threading.Thread(target=self.gui_manager._skip_to_next).start()
        threading.Thread(target=self.gui_manager._load_next_track_details).start()

    def previous_track(self) -> None:
        """Previous track system tray tab."""
        logger.info("SystemTray.previous_track: Previous track clicked")
        
        if self.gui_manager is None:
            logger.warning("SystemTray.play_pause: GUI is not set yet. Please wait a few moments until the GUI is up.")
            return
        
        threading.Thread(target=self.gui_manager.on_previous_button_click).start()

    def exit_app(self) -> None:
        """Exit the app system tray tab."""
        logger.info("SystemTray.exit_app: Exiting the app...")
        self.tray.stop()  
        pid = os.getpid()  
        os.kill(pid, signal.SIGINT) 

    def create_image(self) -> Image:
        """Creates an icon image."""
        image = Image.new('RGB', (64, 64), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill=(0, 0, 0))
        logger.info("SystemTray.create_image: Image created successfully")
        return image

    def run(self) -> None:
        """Runs the system tray."""
        logger.info("SystemTray.run: The tray is running.")
        self.tray.run()
        
        
    


