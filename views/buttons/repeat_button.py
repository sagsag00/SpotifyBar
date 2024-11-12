from .custom_button import CustomButton
from logger import logger

class RepeatButton(CustomButton):
    def __init__(self, master=None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/repeat_off.png", **kwargs)
        
        self.mode = "off"
        
    def on_click(self):
        """Cycle between repeat_off, repeat_context, and repeat_track modes on each click."""
        
        # Cycle through the three modes
        if self.mode == "off":
            self.mode = "context"
            image_path = "resources/buttons/repeat_context.png"
        elif self.mode == "context":
            self.mode = "track"
            image_path = "resources/buttons/repeat_track.png"
        else: 
            self.mode = "off"
            image_path = "resources/buttons/repeat_off.png"
            
        self.spotify.set_repeat_mode(self.mode)
        
        self.tk_image = self.add_image(image_path)
        self.config(image=self.tk_image)
        
        logger.debug("RepeatButton.on_click: Function has completed.")
        
    def load(self):
        mode = self.spotify.get_repeat_mode()
        if mode is None:
            return
        
        if mode == "off":
            self.mode = "off"
            image_path = "resources/buttons/repeat_off.png"
        elif mode == "context":
            self.mode = "context"
            image_path = "resources/buttons/repeat_context.png"
        else: 
            self.mode = "track"
            image_path = "resources/buttons/repeat_track.png"

        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image) 
        
        logger.debug("RepeatButton.load: Function has completed.")