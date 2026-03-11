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

from tkinter import Tk, Event, Label, TclError, PhotoImage, Frame, Button
import os
from PIL import Image, ImageTk, ImageFilter, ImageFile, ImageOps, ImageColor
from screeninfo import get_monitors
from system_tray import SystemTray
import requests
from io import BytesIO
from collections import defaultdict
import colorsys

from api import Spotify
from logger import logger
from gui.gui_manager import GuiManager
from gui.base import Base
from views.scales import PlaybackScale, VolumeScale
from views.buttons import ExitButton, NextButton, PreviousButton, PauseButton, RepeatButton, ShuffleButton, CustomButton
from views.label import SongLabel, BackgroundImage

class App(Base):
    def __init__(self,
                 title: str,
                 icon_path: str,
                 position = "top_start",
                 padding = 10,
                 opacity: float = 1,
                 background_color = "lightgray",
                 background_mode = "default",
                 soft_color_mode = True) -> None:
        logger.debug(f"App.__init__: Initializing application with {title=}, {icon_path=}, {position=}, {padding=}, {opacity=}, {background_color=}")
        self.__position: str = position
        self.__padding: int = padding
        self.__background_mode: str = background_mode
        self.__soft_color_mode: bool = soft_color_mode
        
        self.system_tray = SystemTray()
        self.spotify = Spotify()
        
        super().__init__(title, icon_path, opacity, background_color)

    def _setup(self) -> None:
        """Applies App-specific geometry, background mode and widgets"""
        # Guard: spotify/system_tray may not exist yet on the very first Base.__init__ call
        # if subclass attributes aren't set. The attribute check below handles this safely
        width, height = 370, 170
        super()._setup(geometry=(width, height), func=self._create_buttons, args=(self._window,))
        self._window.withdraw()
        self.__set_initial_position(width, height)
        
        try:
            if self.__background_mode == "song":
                self.set_background_song()
            else:
                self._window.config(bg=self._background_color)
        except TclError:
            logger.error(f"App._setup: Invalid background color '{self._background_color}'")
        
        self._window.bind("<Button-1>", self.__start_move)
        self._window.bind("<B1-Motion>", self.__move_window)
        self._window.bind("<ButtonRelease-1>",
                        lambda e: self.__snap_to_nearest_position(width, height))
        
        logger.info("App._setup: Loading views data.")
        self.gui_manager.load_all()
        
        self._window.deiconify()
        logger.info("App._setup: Window visible and loaded.")
        
        self.system_tray.gui_manager = self.gui_manager
      
    def __start_move(self, event: Event) -> None:
        self._window.x = None
        self._window.y = None
        if event.y <= 20:  # Only drag from top edge
            self._window.x = event.x
            self._window.y = event.y

    def __move_window(self, event: Event) -> None:
        if self._window.x and self._window.y:
            new_x = self._window.winfo_x() + (event.x - self._window.x)
            new_y = self._window.winfo_y() + (event.y - self._window.y)
            self._window.geometry(f"+{new_x}+{new_y}")
        
    def __set_initial_position(self, width, height) -> None:
        """Sets the initial position of the window based on the specified corner.
        Args:
            width (int): The width of the window.
            height (int): The height of the window.
        """
        logger.debug("App.__set_initial_position: Setting initial window position.")
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()

        if self.__position == "top_start":
            x, y = self.__padding, self.__padding
        elif self.__position == "top_end":
            x, y = screen_width - width - 2 * self.__padding - self.__padding//2, self.__padding
        elif self.__position == "bottom_start":
            x, y = self.__padding, screen_height - height - self.__padding
        elif self.__position == "bottom_end":
            x, y = screen_width - width - 2 * self.__padding - self.__padding//2, screen_height - height - self.__padding
        else: 
            x, y = self.__padding, self.__padding

        self._window.geometry(f"{width}x{height}+{x}+{y}")
        logger.debug("App.__set_initial_position: Initial position set to (%d, %d).", x, y)

    def __snap_to_nearest_position(self, width, height):
        """Snaps the window to the closest position: `top_start, top_end, bottom_start, bottom_end`
        
        Args:
            width (int): The width of the window.
            height (int): The height of the window.
        """
        logger.debug("App.__snap_to_nearest_position: Snapping window to nearest position.")

        current_x = self._window.winfo_x()
        current_y = self._window.winfo_y()

        for monitor in get_monitors():
            if (monitor.x <= current_x < monitor.x + monitor.width) and \
            (monitor.y <= current_y < monitor.y + monitor.height):
                screen_x, screen_y = monitor.x, monitor.y
                screen_width, screen_height = monitor.width, monitor.height
                break
        else:
            monitor = get_monitors()[0]
            screen_x, screen_y = monitor.x, monitor.y
            screen_width, screen_height = monitor.width, monitor.height

        positions = {
            "top_start": (screen_x + self.__padding, screen_y + self.__padding),
            "top_end": (screen_x + screen_width - width - 2 * self.__padding - self.__padding // 2, screen_y + self.__padding),
            "bottom_start": (screen_x + self.__padding, screen_y + screen_height - height - self.__padding),
            "bottom_end": (screen_x + screen_width - width - 2 * self.__padding - self.__padding // 2,
                        screen_y + screen_height - height - self.__padding),
        }

        closest_position = min(positions.values(), key=lambda pos: (pos[0] - current_x) ** 2 + (pos[1] - current_y) ** 2)
        self._window.geometry(f"+{closest_position[0]}+{closest_position[1]}")
        logger.debug(f"App.__snap_to_nearest_position: Window snapped to ({closest_position[0]}, {closest_position[1]}).")
        
        
    def set_background_as_image(self):
        """Sets the background image of the app as the current tracks image."""
        logger.debug(f"App.set_background_as_image: Loading and background image.")
        try:
            image_url = self.spotify.get_cover_url()
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            w, h = self._window.winfo_width(), self._window.winfo_height()
            image = self._resize_image(image, w, h)
            image = image.filter(ImageFilter.GaussianBlur(radius=25))
            tk_image = ImageTk.PhotoImage(image)
            
            self.__bg_label = BackgroundImage(self._window, image=tk_image)
            self.__bg_label.image = tk_image  # Keep a reference to prevent garbage collection
            self.__bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.__bg_label.lower()
            logger.info("App.set_background_as_image: Done.")
        except Exception as e:
            logger.error(f"App.set_background_as_image: {e}")

    def set_background_song(self, image_url: str | None = None):
        """Sets the background as the prominent color of the song"""
        logger.debug(f"App.set_background_song: Loading and background image.")
        try:
            if image_url is None:
                image_url = self.spotify.get_cover_url()
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))

            color = self._get_dominant_color(image)
            self._window.configure(background=color)
            self._set_bg_recursive(self._window, color)
            
            inversed_color = self._get_inversed_color(color)
            self._set_textcolor_recursive(self._window, inversed_color)
            self.apply_theme(inversed_color)
            
            self._window.update_idletasks()
            logger.info("App.set_background_song: Done.")
        except Exception as e:
            logger.error(f"App.set_background_song: Error setting background image: {e}")

    def _get_inversed_color(self, color: str) -> str:
        return "#FFFFFF" if self._is_dark(color) else "#000000"
        
    def apply_theme(self, theme_color: str) -> None:
        """Pre-process all button images for the current theme, save to a temp dir."""
        self._recolor_image_folder(src="resources/buttons", dst="resources/buttons_themed", color=theme_color)
        self.__apply_theme(self._window) 

    def __apply_theme(self, widget) -> None:
        if not widget:
            return
        
        for child in widget.winfo_children():
            if isinstance(child, CustomButton) and child.image_path is not None:
                child.refresh_image()
            else:
                self.__apply_theme(child)

    def _recolor_image_folder(self, src: str, dst: str, color: str) -> None:
        color = ImageColor.getrgb(color)
        dim = tuple(int(c * 0.6) for c in color)
        os.makedirs(dst, exist_ok=True)
        
        for fname in os.listdir(src):
            if not fname.endswith(".png"):
                continue
            image = Image.open(os.path.join(src, fname)).convert("RGBA")
            recolored = self._recolor_image(image, color, dim)
            recolored.save(os.path.join(dst, fname))
    
    def _recolor_image(self, image: Image, inversed: tuple[int, int, int], dim: tuple[int]) -> Image:
        gray = ImageOps.grayscale(image)
        result = Image.new("RGBA", image.size)
        
        pixels = [
            (
                int(dim[0] * (1 - t) + inversed[0] * t),
                int(dim[1] * (1 - t) + inversed[1] * t),
                int(dim[2] * (1 - t) + inversed[2] * t),
                a
            )
            for g, a in zip(gray.getdata(), image.getchannel("A").getdata())
            for t in (g / 255,)
        ]
            
        result.putdata(pixels)
        return result
    
    def _set_textcolor_recursive(self, widget, color: str) -> None:
        try:
            widget.configure(fg=color)
        except:
            pass

        for child in widget.winfo_children():
            self._set_textcolor_recursive(child, color)

    def _set_bg_recursive(self, widget, color: str) -> None:
        try:
            widget.configure(bg=color)
        except:
            pass

        for child in widget.winfo_children():
            self._set_bg_recursive(child, color)
            
            if isinstance(child, Button):
                child.configure(activebackground=color)

    def _is_dark(self, hex_color: str) -> bool:
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (0.299 * r + 0.587 * g + 0.114 * b) < 128

    def _get_dominant_color(self, image: ImageFile) -> str:
        """Gets the prominent color of an image."""
        image = image.convert("RGB").resize((150, 150))
        counts: dict = defaultdict(int)
        for r, g, b in image.getdata():
            counts[(r // 16, g // 16, b // 16)] += 1
            
        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5][::-1]
        chosen_bucket, chosen_count = None, 0
        
        for bucket, count in top:
            r, g, b = (x* 16 + 8 for x in bucket)
            brightness = 0.299*r + 0.586*g + 0.114*b
            if brightness < 40 and count < chosen_count * 2.5:
                continue
            chosen_bucket, chosen_count = bucket, count
            
        if chosen_bucket is None:
            chosen_bucket = top[0][0]

        r, g, b = (x * 16 + 8 for x in chosen_bucket)
        color = (self._soften_color((r, g, b)) if self.__soft_color_mode else (r, g, b))
        return "#%02x%02x%02x" % color

    def _soften_color(self, rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        r, g, b = (x / 255 for x in rgb)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        s = min(s, 0.95)
        v = min(v, 0.87)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return tuple([int(r*255), int(g*255), int(b*255)])

    def _resize_image(self, image: PhotoImage, fixed_width: int, fixed_height: int) -> PhotoImage:
        return image.resize((fixed_width, fixed_height), Image.Resampling.LANCZOS)

    def _create_buttons(self, window: Tk) -> None:
        """A function that creates the spotify buttons for a given window."""
        logger.debug("App._create_buttons: Creating buttons.")
        self.playback_scale = PlaybackScale(window)
        self.playback_scale.place(relx=0.5, rely=0.9, anchor="center")
        self.volume_scale = VolumeScale(window)
        self.volume_scale.place(relx=1.0, rely=0.54, x=-10, anchor="e")

        self.exit_button = ExitButton(window, width=100)
        self.exit_button.place(relx=1.0, rely=0.0, x=0, y=0, anchor="ne")
        
        window.update_idletasks() 
        window.update() 
        
        button_frame = Frame(window, bg=window.cget('bg'))
        button_frame.place(relx=0.478, y=135, anchor="center")
                
        self.shuffle_button = ShuffleButton(button_frame)
        self.shuffle_button.pack(side="left", padx=1)
        
        self.prev_button = PreviousButton(button_frame)
        self.prev_button.pack(side="left", padx=1)

        self.pause_button = PauseButton(button_frame)
        self.pause_button.pack(side="left", padx=1)

        self.next_button = NextButton(button_frame)
        self.next_button.pack(side="left", padx=1)

        self.repeat_button = RepeatButton(button_frame)
        self.repeat_button.pack(side="left", padx=1)
        
        try:
            image = Image.open("./resources/images/place_holder.png")
        except FileNotFoundError:
            logger.error("App._create_buttons: Placeholder image not found.")
        image.thumbnail((85, 85))
        tk_image = ImageTk.PhotoImage(image)
        self.__song_pic = Label(window, image=tk_image, bg="black") 
        self.__song_pic.image = tk_image 
        self.__song_pic.place(x=30, y=20)
        
        window.update_idletasks()
        self.song_name = SongLabel(window, max_width=200)
        self.song_name.place(x=self.__song_pic.winfo_x() + 96, y=self.__song_pic.winfo_y() + 8)
        self.song_name.title = "Song Label"
        
        window.update_idletasks()
        self.artist_name = SongLabel(window, font_size=10, is_bold=False, max_width=200)
        self.artist_name.place(x=self.song_name.winfo_x(), y=self.song_name.winfo_y() + 22)
        self.artist_name.title = "Artist Label"
        
        window.update_idletasks()
        self.album_name = SongLabel(window, font_size=10, is_bold=False, max_width=125)
        self.album_name.place(x=self.artist_name.winfo_x(), y=self.artist_name.winfo_y())
        self.album_name.title = "Album Label"
        
        self.gui_manager = GuiManager(
                window, on_next_song=self._on_next_song, playback_scale=self.playback_scale, volume_scale=self.volume_scale,
                exit_button=self.exit_button, pause_button=self.pause_button, next_button=self.next_button,
                repeat_button=self.repeat_button, previous_button=self.prev_button, shuffle_button=self.shuffle_button,
                song_pic=self.__song_pic, song_label=self.song_name, artist_label=self.artist_name,
                album_label=self.album_name
                )
        
        self.system_tray.gui_manager = self.gui_manager 

        logger.debug("App._create_buttons: Done.")

    def _on_next_song(self, image_url: str | None = None) -> None:
        """Called on the next song"""
        if self.__background_mode == "song":
            self.set_background_song(image_url)


    
# Run the application
if __name__ == "__main__":
    App("test", "icon.ico", position="top_end", padding=10).run()