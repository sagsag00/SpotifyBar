from .custom_button import CustomButton
from typing import Callable
from logger import logger

class PreviousButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/previous.png", **kwargs)
        
        self.callable: Callable[..., None] = None
      
    def set_callback(self, callable: Callable[..., None]) -> None:
        self.callable = callable
        logger.debug("PreviousButton.set_callback: Function has completed.")

    
    def on_click(self):
        self.callable()
        
        logger.debug("PreviousButton.on_click: Function has completed.")