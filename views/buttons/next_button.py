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
from typing import Callable
from logger import logger
import threading

class NextButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/next.png", **kwargs)
    
        self.callable: Callable[..., None] = None
           
    def set_callback(self, callable: Callable[..., None]) -> None:
        self.callable = callable  
           
        logger.debug("NextButton.set_callback: Function has completed.") 
     
    def on_click(self):
        threading.Thread(target=self.callable).start()
        logger.debug("NextButton.on_click: Function has completed.") 
        
        