from .custom_button import CustomButton
from typing import Callable
from logger import logger
import threading

class NextButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/next.png", **kwargs)
    
        self.callable: Callable = None
           
    def set_callable(self, callable: Callable) -> None:
        self.callable = callable  
           
        logger.debug("NextButton.set_callable: Function has completed.") 
     
    def on_click(self):
        threading.Thread(target=self.callable).start()
        logger.debug("NextButton.on_click: Function has completed.") 
        
        