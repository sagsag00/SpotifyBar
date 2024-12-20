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

from tkinter import Tk, Event, Label, TclError, PhotoImage
import ctypes
from views.scales import PlaybackScale, VolumeScale
from views.buttons import ExitButton, NextButton, PreviousButton, PauseButton, RepeatButton, ShuffleButton
from views.label import SongLabel, BackgroundImage
from PIL import Image, ImageTk, ImageFilter
from gui_manager import GuiManager
from logger import logger
from screeninfo import get_monitors
from system_tray import SystemTray
import requests
from io import BytesIO
from api import Spotify

class App():
    def __init__(self, title: str, icon_path: str, position = "top_start", padding = 10, opacity: float = 1, background_color = "lightgray") -> None:
        logger.debug(f"App.__init__: Initializing application with {title=}, {icon_path=}, {position=}, {padding=}, {opacity=}, {background_color=}")
        self.__window: Tk = Tk()
        self.__title: str = title
        self.__icon_path: str = icon_path
        self.__opacity: float = opacity
        self.__position: str = position
        self.__padding: int = padding 
        self.__background_color: str = background_color
        
        # Creating a system tray for later use.
        self.system_tray = SystemTray()
        self.spotify = Spotify()
        self.__setup()

    def __setup(self) -> None:
        """The setup for the window."""
        logger.debug("App.__setup: Starting window creation.")
        window: Tk = self.__window
        try:
            window.iconbitmap(self.__icon_path) 
        except TclError:
            logger.error(f"App.__setup: Icon file was not found on '{self.__icon_path}'")
        window.title(self.__title)

        width, height = 370, 170
        
        window.geometry(f"{width}x{height}")
        try:
            window.config(bg=self.__background_color)
        except TclError:
            logger.error(f"App.__setup: Inavlid background color '{self.__background_color}'")
        try:
            window.attributes("-alpha", self.opacity)
        except TclError:
            logger.error(f"App.__setup: Inavlid opacity '{self.opacity}'")
    
        self.__make_borderless()
        self.__set_rounded_corners()
        window.wm_attributes("-topmost", 1)
        self.__window.after(500, self.__make_borderless)  # Delay to ensure window is created
        self.__window.after(500, self.__set_rounded_corners)  # Delay for rounded corners
        
        window.update()
        actual_width = window.winfo_width()  
        actual_height = window.winfo_height()
        self.__set_initial_position(actual_width, actual_height)

        # Binding the mouse motions for dragging and snapping to locations.
        logger.debug("App.__setup: Loading mouse motions.")
        window.bind("<Button-1>", self.__start_move)
        window.bind("<B1-Motion>", self.__move_window)
        window.bind("<ButtonRelease-1>", lambda event: self.__snap_to_nearest_position(actual_width, actual_height))
        
        window.withdraw() # Hiding the window while loading.

        self.__create_buttons(window)
        # Making the window visible and then hiding again for specific animation (a friend asked for this).
        window.deiconify() 
        window.withdraw()

        logger.info("App.__setup: Loading views data.")
        self.gui_manager.load_all()
        logger.debug("App.__setup: Views data loaded.")
        
        window.deiconify()
        
        logger.info("App.__setup: Window is visible and loaded.")
        
        self.window = window
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def set_background_as_image(self):
        """Sets the background image of the app as the current tracks image."""
        logger.debug(f"App.set_background_as_image: Loading and background image.")
        try:
            image_url = self.spotify.get_cover_url()
            response = requests.get(image_url)
            img_data = response.content
            image = Image.open(BytesIO(img_data))
            
            # Resize to match the window size
            window_width = self.__window.winfo_width()
            window_height = self.__window.winfo_height()
            image = self._resize_image(image, window_width, window_height)
            
            # Apply a blur effect
            image = image.filter(ImageFilter.GaussianBlur(radius=25))  # Adjust radius for more/less blur
            
            # Convert to Tkinter-compatible image
            tk_image = ImageTk.PhotoImage(image)
            
            # Set the background image
            self.__bg_label = BackgroundImage(self.__window, image=tk_image)
            self.__bg_label.image = tk_image  # Keep a reference to prevent garbage collection
            self.__bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.__bg_label.lower()
            
            logger.info("App.set_background_as_image: Background image set successfully.")
        except Exception as e:
            logger.error(f"App.set_background_as_image: Error setting background image: {e}")
            
    def _resize_image(self, image: PhotoImage, fixed_width: int, fixed_height: int) -> PhotoImage:
        """Resize the image."""
        logger.debug("GuiManager._resize_image: Resizing the image without keeping the aspect ratio.")
        
        # Resize the image to the fixed dimensions
        image = image.resize((fixed_width, fixed_height), Image.Resampling.LANCZOS)
        
        logger.debug("GuiManager._resize_image: Function has completed.")
        return image

        
    def on_close(self):
        """Actions to perform when the window is closed"""
        logger.info("App closed.")
        self.window.destroy() 
        
    def __create_buttons(self, window: Tk) -> None:
        """A function that creates the spotify buttons for a given window."""
        logger.debug("App.__create_buttons: Creating buttons.")
        self.playback_scale = PlaybackScale(window)
        self.playback_scale.place(relx=0.5, rely=0.9, anchor="center")
        self.volume_scale = VolumeScale(window)
        self.volume_scale.place(relx=1.0, rely=0.54, x=-10, anchor="e")

        self.exit_button = ExitButton(window, width=100)
        self.exit_button.place(relx=1.0, rely=0.0, x=0, y=0, anchor="ne")
        
        window.update_idletasks() # Update the window.
        self.pause_button = PauseButton(window)
        self.pause_button.place(relx=0.478, y=self.playback_scale.winfo_y() - 15, anchor="center")
        
        window.update_idletasks()
        self.next_button = NextButton(window)
        self.next_button.place(x=self.pause_button.winfo_x() + self.pause_button.winfo_width() + 10, y=self.pause_button.winfo_y())
        window.update_idletasks()
        self.repeat_button = RepeatButton(window)
        self.repeat_button.place(x=self.next_button.winfo_x() + 28, y=self.pause_button.winfo_y() + 2)
        
        window.update_idletasks()
        self.prev_button = PreviousButton(window)
        self.prev_button.place(x=self.pause_button.winfo_x() - 21, y=self.pause_button.winfo_y())
        window.update_idletasks()
        self.shuffle_button = ShuffleButton(window)
        self.shuffle_button.place(x=self.prev_button.winfo_x() - 28, y=self.pause_button.winfo_y() + 2)
        
        image = Image.open("./resources/images/place_holder.png")
        image.thumbnail((85, 85))
        tk_image = ImageTk.PhotoImage(image)

        self.__song_pic = Label(window, image=tk_image, bg="black") 
        self.__song_pic.image = tk_image 
        self.__song_pic.pack(padx=30, pady=20, side="left", anchor="nw")
        
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
        
        logger.debug("App.__create_buttons: Finished creating buttons.")
        
        # Create GUIManager
        self.gui_manager = GuiManager(
                window, playback_scale=self.playback_scale, volume_scale=self.volume_scale,
                exit_button=self.exit_button, pause_button=self.pause_button, next_button=self.next_button,
                repeat_button=self.repeat_button, previous_button=self.prev_button, shuffle_button=self.shuffle_button,
                song_pic=self.__song_pic, song_label=self.song_name, artist_label=self.artist_name,
                album_label=self.album_name
                )
        
        self.system_tray.gui_manager = self.gui_manager # Updates the system_trays gui_manager to match this one

    def __set_initial_position(self, width, height) -> None:
        """Sets the initial position of the window based on the specified corner.
        Args:
            width (int): The width of the window.
            height (int): The height of the window.
        """
        logger.debug("App.__set_initial_position: Setting initial window position.")
        screen_width = self.__window.winfo_screenwidth()
        screen_height = self.__window.winfo_screenheight()

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

        self.__window.geometry(f"{width}x{height}+{x}+{y}")
        logger.debug("App.__set_initial_position: Initial position set to (%d, %d).", x, y)

    def __make_borderless(self) -> None:
        """Makes the window borderless."""
        logger.debug("App.__make_borderless: Making window borderless.")
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        GWL_STYLE = -16
        WS_VISIBLE = 0x10000000
        WS_POPUP = 0x80000000
        result = ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, WS_VISIBLE | WS_POPUP)
        if result == 0:
            logger.error("SetWindowLongW failed to make the window borderless.")
        else:
            logger.debug("Window borderless applied successfully.")

    def __set_rounded_corners(self) -> None:
        """Sets the rounded corners."""
        logger.debug("App.__set_rounded_corners: Setting rounded corners.")
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMNCRP_ROUND = 2
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMNCRP_ROUND)),
            ctypes.sizeof(ctypes.c_int)
        )
        if result != 0:
            logger.error("DwmSetWindowAttribute failed to set rounded corners.")
        else:
            logger.debug("Rounded corners applied successfully.")

    def __start_move(self, event: Event):
        """Starts to move the screen if clicked on the edges."""
        logger.debug("App.__start_move: Initiating window move on mouse click.")
        self.__window.x = None
        self.__window.y = None  

        if event.y <= 20:
            self.__window.x = event.x
            self.__window.y = event.y
            
    def __move_window(self, event: Event):
        """Moves the window on left click drag."""
        # If the class is not of a window class, don't trigger the moving event.
        if not event.widget.winfo_class() == "Tk" and not isinstance(event.widget, BackgroundImage):
            return
        
        if self.__window.x and self.__window.y:
            # Calculate new position
            new_x = self.__window.winfo_x() + (event.x - self.__window.x)
            new_y = self.__window.winfo_y() + (event.y - self.__window.y)

            # Move the window to the new position immediately
            self.__window.geometry(f"+{new_x}+{new_y}")
            logger.debug(f"App.__move_window: Moving window to ({new_x}, {new_y}).")  

    def __snap_to_nearest_position(self, width, height):
        """Snaps the window to the closest position: `top_start, top_end, bottom_start, bottom_end`
        
        Args:
            width (int): The width of the window.
            height (int): The height of the window.
        """
        logger.debug("App.__snap_to_nearest_position: Snapping window to nearest position.")

        # Get current window position
        current_x = self.__window.winfo_x()
        current_y = self.__window.winfo_y()

        # Find the monitor that the window is currently on
        for monitor in get_monitors():
            if (monitor.x <= current_x < monitor.x + monitor.width) and \
            (monitor.y <= current_y < monitor.y + monitor.height):
                screen_x, screen_y = monitor.x, monitor.y
                screen_width, screen_height = monitor.width, monitor.height
                break
        else:
            # Default to primary monitor if no specific match is found
            monitor = get_monitors()[0]
            screen_x, screen_y = monitor.x, monitor.y
            screen_width, screen_height = monitor.width, monitor.height

        # Define possible snap positions based on the monitor's size and position
        positions = {
            "top_start": (screen_x + self.__padding, screen_y + self.__padding),
            "top_end": (screen_x + screen_width - width - 2 * self.__padding - self.__padding // 2, screen_y + self.__padding),
            "bottom_start": (screen_x + self.__padding, screen_y + screen_height - height - self.__padding),
            "bottom_end": (screen_x + screen_width - width - 2 * self.__padding - self.__padding // 2,
                        screen_y + screen_height - height - self.__padding),
        }

        # Find the closest position to snap to
        closest_position = min(positions.values(), key=lambda pos: (pos[0] - current_x) ** 2 + (pos[1] - current_y) ** 2)

        # Move the window to the closest position
        self.__window.geometry(f"+{closest_position[0]}+{closest_position[1]}")
        logger.debug(f"App.__snap_to_nearest_position: Window snapped to ({closest_position[0]}, {closest_position[1]}).")
        
    @property
    def opacity(self) -> float:
        logger.debug("App.opacity: Getting opacity value.")
        return self.__opacity
    
    @opacity.setter
    def opacity(self, new_opacity: float) -> None:
        logger.debug(f"App.opacity: Setting opacity to {new_opacity:.2f}.")
        self.__opacity = min(max(new_opacity, 0), 1)
        self.__window.attributes("-alpha", self.__opacity)
        logger.info(f"App.opacity: Opacity set to {self.__opacity:.2f}.")
        
    @opacity.deleter
    def opacity(self) -> None:
        del self.__opacity
        
    def run(self) -> None:
        """Runs the main application loop."""
        
        logger.info("App.run: Starting application loop.")
        try:
            self.__window.mainloop()
            logger.info("App.run: Application loop running.")
        except Exception as e:
            logger.error(f"App.run: Error occurred in main loop: {e}")
        finally:
            logger.info("App.run: Application loop ended.")
    
# Run the application
if __name__ == "__main__":
    App("test", "icon.ico", position="top_end", padding=10).run()