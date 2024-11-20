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

from .custom_button import CustomButton
from views.scales import PlaybackScale
from typing import Callable, Union
from logger import logger
import threading

class PauseButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None: 
        super().__init__(master, "resources/buttons/pause.png", **kwargs)
        
        self._is_active = True
        self.callback: Callable[[bool], None] = None
        
    def set_callback(self, callback: Callable[[bool], None]):
        self.callback = callback
        
        logger.debug("PauseButton.set_callback function has completed.") 
        
    def on_click(self):
        """Toggle between pause and resume images on each click."""
        if self._is_active:
            threading.Thread(target=self.spotify.pause())
            if self.callback:
                threading.Thread(target=self.callback, args=(True,)).start()
        else:
            threading.Thread(target=self.spotify.play())
            if self.callback:
                threading.Thread(target=self.callback, args=(False,)).start()
        
        self._is_active = not self._is_active  
        threading.Thread(target=self.change_image())
        
        logger.debug("PauseButton.on_click: Function has completed.") 

    def load(self):
        is_active = self.spotify.is_player_active()
        
        if is_active is None:
            return
        
        self._is_active = is_active  
        image_path = "resources/buttons/pause.png" if self._is_active else "resources/buttons/resume.png"
        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image)   
        
        logger.debug("PauseButton.on_click: Function has completed.")  
    
    def change_image(self) -> None:
        image_path = "resources/buttons/pause.png" if self._is_active else "resources/buttons/resume.png"
        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image)
        
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    @is_active.setter
    def is_active(self, new_val: bool) -> None:
        if isinstance(new_val, bool) and new_val != self._is_active:
            self._is_active = not self._is_active  
            threading.Thread(target=self.change_image())
            
            logger.debug("PauseButton.is_active.setter: Function has completed.")
        
        
        