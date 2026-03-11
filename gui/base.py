# Copyright 2026 Sagi Tsafrir

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from logger import logger
from tkinter import Tk, TclError, Event
import ctypes
from typing import Callable, Union

class Base():
    def __init__(self,
                 title: str,
                 icon_path: str,
                 opacity: float = 1,
                 background_color: str = "lightgray") -> None:
        logger.debug(f"Base.__init__: Initializing with {title=}, {icon_path=}, {opacity=}, {background_color=}")
        self._window: Tk = Tk()
        self._title: str = title
        self._icon_path: str = icon_path
        self._opacity: float = opacity
        self._background_color: str = background_color

        self._setup()
        
    def _setup(self, geometry: tuple[int, int], func: Union[Callable, None] = None, args: Union[tuple, None] = None) -> None:
        """Base setup: icon, title, background, borderless, rounded, topmost, bindings"""
        logger.debug("Base._setup: Starting base window setup.")
        window = self._window
        try:
            window.iconbitmap(self._icon_path)
        except TclError:
            logger.error(f"Base._setup: Icon file not found at '{self._icon_path}'") 
        window.title(self._title)
        
        window.geometry(f"{geometry[0]}x{geometry[1]}")
        try:
            window.config(bg=self._background_color)
        except TclError:
            logger.error(f"Base._setup: Invalid background color '{self._background_color}")
            
        try:
            window.attributes("-alpha", self._opacity)
        except TclError:
            logger.error(f"Base._setup: Invalid opacity '{self._opacity}'")
            
        self._make_borderless()
        self._set_rounded_corners()
        window.wm_attributes("-topmost", 1)
        window.after(500, self._make_borderless)
        window.after(500, self._set_rounded_corners)
        
        window.update()
        window.bind("<Button-1>", self._start_move)
        window.bind("<B1-Motion>", self._move_window)
        
        window.withdraw()
        
        if func is not None:
            func(*(args or ()))
            
        window.deiconify() 
        self._window = window
        window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_close(self) -> None:
        logger.info("Base: Window closed.")
        self._window.destroy()
        
    def _make_borderless(self) -> None:
        logger.debug("Base._make_borderless: Making window borderless.")
        
        hwnd = ctypes.windll.user32.FindWindowW(None, self._title)
        
        GWL_STYLE = -16
        WS_VISIBLE = 0x10000000
        WS_POPUP = 0x80000000
        
        result = ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, WS_VISIBLE | WS_POPUP)
        if result == 0:
            logger.error("Base._make_borderless: SetWindowLongW failed.")
        else:
            logger.debug("Base._make_borderless: Applied successfully.")

    def _set_rounded_corners(self) -> None:
        logger.debug("Base._set_rounded_corners: Setting rounded corners.")
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMNCRP_ROUND = 2
        hwnd = ctypes.windll.user32.FindWindowW(None, self._title)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMNCRP_ROUND)),
            ctypes.sizeof(ctypes.c_int)
        )
        if result != 0:
            logger.error("Base._set_rounded_corners: DwmSetWindowAttribute failed.")
        else:
            logger.debug("Base._set_rounded_corners: Applied successfully.")
            
    def _start_move(self, event: Event) -> None:
        self._window.x = event.x
        self._window.y = event.y

    def _move_window(self, event: Event) -> None:
        if self._window.x is not None and self._window.y is not None:
            new_x = self._window.winfo_x() + (event.x - self._window.x)
            new_y = self._window.winfo_y() + (event.y - self._window.y)
            self._window.geometry(f"+{new_x}+{new_y}")
            
    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, new_opacity: float) -> None:
        self._opacity = min(max(new_opacity, 0), 1)
        self._window.attributes("-alpha", self._opacity)
        logger.info(f"Base.opacity: Set to {self._opacity:.2f}.")

    def run(self) -> None:
        logger.info("Base.run: Starting main loop.")
        try:
            self._window.mainloop()
        except Exception as e:
            logger.error(f"Base.run: Error in main loop: {e}")
        finally:
            logger.info("Base.run: Main loop ended.")