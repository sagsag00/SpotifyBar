from .custom_button import CustomButton
from typing import Callable
from logger import logger

class PreviousButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/previous.png", **kwargs)
        
        self.callable: Callable = None
      
    def set_callable(self, callable: Callable) -> None:
        self.callable = callable
        logger.debug("PreviousButton.set_callable: Function has completed.")

    
    def on_click(self):
        self.callable()
        
        logger.debug("PreviousButton.on_click: Function has completed.")