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

from tkinter import Tk, Canvas, Event
from api import Spotify
from logger import logger

class Scale(Canvas):
    def __init__(self, master: Tk = None, orientation: str = "vertical", **kwargs):
        orientations = ("vertical", "horizontal")
        self.is_vertical = True
        
        if orientation not in orientations:
            logger.error(f"Scale.__init__: Invalid orientation: {orientation}")
            raise TypeError(f"orientation {orientation} invalid")
        
        self._width = kwargs["width"] = 15
        kwargs["height"] = 130
        self._height = kwargs["height"] - 15
        self._scale_value = kwargs["height"] // 2   
            
        if orientation == orientations[1]:
            kwargs["width"] = 187
            self._width = kwargs["width"] - 15
            self._height = kwargs["height"] = 20   
            self._scale_value = kwargs["width"] // 2
            self.is_vertical = False
   
        kwargs["bg"] = master.cget("bg")     
        kwargs["highlightthickness"] = 0
        kwargs["bd"] = 0
        
        super().__init__(master, **kwargs)
        
        logger.debug(f"Scale.__init__: Scale initialized with orientation={orientation}, width={self._width}, height={self._height}")
        
        if self.is_vertical:
            self._create_vertical()
            self.bind("<B1-Motion>", self._move_button_vertical)
        else:
            self._create_horizontal()
            self.bind("<B1-Motion>", self._move_button_horizontal)
            
        self.spotify = Spotify()
        logger.debug("Scale.__init__: Spotify instance created in volume control.")
             
    def _create_vertical(self):
        y_pos = self._y_position()
        self._scale_line_vertical = self.create_line(7.5, 0, 7.5, self._height, fill="gray", width=3)
        self.button = self.create_oval(2.5, y_pos, 12.5, y_pos + 10,
                                        fill="darkgray", outline="darkgray", width=2)
        logger.debug("Scale._create_vertical: Vertical scale created.")
        
    def _create_horizontal(self):
        x_pos = self._x_position()
        self._scale_line_horizontal = self.create_line(0, 7.5, self._width, 7.5, fill="gray", width=3)
        self.button = self.create_oval(x_pos, 2.5, x_pos + 10, 12.5,
                                        fill="darkgray", outline="darkgray", width=2)
        logger.debug("Scale._create_horizontal: Horizontal scale created.")
        
    def _y_position(self) -> int:
        """Calculate the Y position of the button based on current value."""
        return self._height - (self._scale_value)
    
    def _x_position(self) -> int:
        """Calculate the Y position of the button based on current value."""
        return self._width - (self._scale_value)
    
    def _move_button_vertical(self, event: Event = None) -> None:
        """Move the button and update the value based on the mouse position."""
        new_y = self._scale_value
        if event:
            new_y = event.y
        max_value = 0
        min_value = self._height
        if max_value <= new_y <= min_value:
            self.coords(self.button, 2.5, new_y, 12.5, new_y + 10)
            self._scale_value = 100 - int((new_y / self._height) * 100)
            logger.debug(f"Scale._move_button_vertical: Vertical button moved to {new_y}, scale value updated to {self._scale_value}")
      
    def _move_button_horizontal(self, event: Event = None) -> None:
        """Move the button and update the value based on the mouse position."""
        new_x = self._scale_value
        if event:
            new_x = event.x
        max_value = 0
        min_value = self._width
        if max_value <= new_x <= min_value:
            self.coords(self.button, new_x, 2.5, new_x + 10, 12.5)
            self._scale_value = int((new_x / self._width) * 100)   
            logger.debug(f"Scale._move_button_horizontal: Horizontal button moved to {new_x}, scale value updated to {self._scale_value}")   
    
    @property
    def value(self):
        return self._scale_value
    
    @value.setter
    def value(self, new_val: int):
        if not new_val:
            new_val = 50
            logger.debug("No value passed, defaulting to 50.")
        
        logger.debug(f"Scale.value.setter: Setting scale value to {new_val}")
        
        if self.is_vertical:
            if new_val <= 1:
                self._scale_value = self._height - new_val
                self._move_button_vertical()
                return
            self._scale_value = round(abs(100 - new_val) / 100 * self._height + 0.5)
            self._move_button_vertical()
        else:
            self._scale_value = round(new_val / 100 * self._width + 0.5)
            self._move_button_horizontal()
    
    @value.deleter
    def value(self):
        del self._scale_value