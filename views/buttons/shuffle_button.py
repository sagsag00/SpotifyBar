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
from logger import logger

class ShuffleButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/shuffle_off.png", **kwargs)
        
        self.is_active = False
        
    def on_click(self):
        """Toggle between pause and resume images on each click."""
        if self.is_active:
            self.spotify.set_shuffle_mode("off")
        else:
            self.spotify.set_shuffle_mode("on")
        
        self.is_active = not self.is_active  
        image_path = "resources/buttons/shuffle_on.png" if self.is_active else "resources/buttons/shuffle_off.png"
        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image)
        
        logger.debug("ShuffleButton.on_click: Function has completed.")  
        
    def load(self):
        is_active = self.spotify.is_shuffle_active()
        if is_active is None:
            return
        self.is_active = is_active  
        image_path = "resources/buttons/shuffle_on.png" if self.is_active else "resources/buttons/shuffle_off.png"
        self.tk_image = self.add_image(image_path)  
        self.config(image=self.tk_image) 
        
        logger.debug("ShuffleButton.load: Function has completed.")  