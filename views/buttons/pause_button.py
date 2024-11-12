from .custom_button import CustomButton
from views.scales import PlaybackScale
from typing import Callable
from logger import logger
import threading

class PauseButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None: 
        super().__init__(master, "resources/buttons/pause.png", **kwargs)
        
        self.is_active = True
        self.callback: Callable = None
        
    def set_callback(self, callback: Callable):
        self.callback = callback
        
        logger.debug("PauseButton.set_callback function has completed.") 
        
    def on_click(self):
        """Toggle between pause and resume images on each click."""
        if self.is_active:
            threading.Thread(target=self.spotify.pause())
            if self.callback:
                threading.Thread(target=self.callback, args=(True,)).start()
        else:
            threading.Thread(target=self.spotify.play())
            if self.callback:
                threading.Thread(target=self.callback, args=(False,)).start()
        
        self.is_active = not self.is_active  
        threading.Thread(target=self.change_image())
        
        logger.debug("PauseButton.on_click: Function has completed.") 

    def load(self):
        is_active = self.spotify.is_player_active()
        
        if is_active is None:
            return
        
        self.is_active = is_active  
        image_path = "resources/buttons/pause.png" if self.is_active else "resources/buttons/resume.png"
        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image)   
        
        logger.debug("PauseButton.on_click: Function has completed.")  
            
    def is_playback_active(self) -> bool:
        return self.is_active
    
    def change_image(self) -> None:
        image_path = "resources/buttons/pause.png" if self.is_active else "resources/buttons/resume.png"
        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image)