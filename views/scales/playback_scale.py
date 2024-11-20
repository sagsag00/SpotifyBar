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

from .scale import Scale
from tkinter import Label, font, Tk
from views.label import TimeLabel
from typing import Callable
from logger import logger

class PlaybackScale(Scale):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "horizontal", **kwargs)    
        
        self.master: Tk = master
        self._timer_id: str = None
        self.stop_callback: Callable = None
        self._animation_id: str = None
        
        custom_font = font.Font(family="David", size=8, weight="bold")
        
        self.curr_time = TimeLabel(master, text="0:00", foreground="gray", bg=master.cget("bg"), font=custom_font)
        self.end_time = TimeLabel(master, text="99:99", foreground="gray", bg=master.cget("bg"), font=custom_font)
        
        self.bind("<B1-Motion>", self._move_button_horizontal)
        self.bind("<ButtonRelease-1>", self._on_button_release)
        
        logger.debug("PlaybackScale.__init__: PlaybackScale initialized.")
    
    def place(self, **kwargs):
        """Custom function that uses the parent function as a base. 
            Places two more buttons after to create a playback timeline.
        """
        super().place(**kwargs)
        
        self.master.update_idletasks()
        scale_x = self.winfo_x()
        scale_y = self.winfo_y()
        scale_width = self.winfo_width()
        
        self.curr_time.place(x=scale_x - 15, y=scale_y + 8, anchor="center") 
        self.end_time.place(x=scale_x + scale_width + 15, y=scale_y + 8, anchor="center")
        
        logger.debug(f"PlaybackScale.place: PlaybackScale placed at x: {scale_x}, y: {scale_y}, width: {scale_width}")
        
    def set_callback(self, callback: Callable) -> None:
        """Sets the callback to be called when stop_timer is executed."""
        self.stop_callback = callback
        logger.debug("PlaybackScale.set_stop_callback: Stop callback set.")
    
    def start(self):
        """Starts the timer and playback moving animation from scratch, while syncing it with spotify."""
        self.load()
        playback_state = self.spotify.get_playback_state_ms()
        if not playback_state:
            logger.warning("PlaybackScale.start: No playback state found.")
            return
        delay =  playback_state % 1000 + 1000
        self.start_timer(delay)
        self._start_animation_playback_position()

        logger.debug("PlaybackScale.start: Playback started.")
    
    def start_timer(self, time_difference_ms: int = 0) -> None:
        """Starts the timer and updates every second. Prevents multiple timers."""
        # Prevent multiple timers from running
        if getattr(self, "_is_timer_running", False):
            return  # Exit if the timer is already running
        
        self._is_timer_running = True  # Mark the timer as running
        
        def timer_tick():
            """Internal function to handle the timer's ticking logic."""
            self.curr_time.seconds += 1
            if self.curr_time.seconds >= 60:
                self.curr_time.seconds = 0
                self.curr_time.minutes += 1

            # Sync every 20 seconds
            if self.curr_time.seconds % 20 == 0 and self.curr_time.seconds != 0:
                self.load()

            # Check if we've reached the end time
            if self.curr_time >= self.end_time:
                logger.critical("Hi")
                self.load()
                self.stop_timer()
                return

            # Stop one second before the end of the song
            if self.curr_time + 1 >= self.end_time:
                self.stop_timer()
                self.stop_callback()
                logger.debug("PlaybackScale.start_timer: End time reached, stopping playback.")
                return

            # Schedule the next tick
            self._timer_id = self.after(1000, timer_tick)
            logger.debug("PlaybackScale.start_timer: Timer tick.")

        # Start the first tick with the optional time difference delay
        self._timer_id = self.after(time_difference_ms or 1000, timer_tick)

    def stop_timer(self) -> None:
        """Stops the timer."""
        self._stop_animation()
        if getattr(self, "_is_timer_running", False):
            self._is_timer_running = False 
            if self._timer_id is not None:
                self.after_cancel(self._timer_id)
                self._timer_id = None
                logger.debug("PlaybackScale.stop_timer: Timer stopped.")
            
    def reset(self) -> None:
        """Resets the timer to 00:00"""
        self.stop_timer()
        self.curr_time.curr_time = "00:00"
        self.start_timer()
        self._start_animation_playback_position()
        
        logger.debug("PlaybackScale.reset: PlaybackScale reset.")
            
    def load(self):
        """Loads the current playback current time and end time to the current playing track."""
        self.curr_time.curr_time = self.spotify.get_playback_state_timer()
        self.end_time.curr_time = self.spotify.get_song_duration_timer()
        self.value = (self.curr_time.miliseconds / (self.end_time.miliseconds + 0.1)) * 100

        if self.curr_time.curr_time > self.end_time.curr_time:
            self.stop_timer()
        logger.debug(f"PlaybackScale.load: Loaded current time: {self.curr_time.curr_time}, end time: {self.end_time.curr_time}.")
        
    def _move_button_horizontal(self, event=None) -> None:
        """Moves the button to the given position, if there was an event, stop the animation and change the timer to the current events time."""
        super()._move_button_horizontal(event)

        if event:
            self.curr_time.miliseconds = int(self.end_time.miliseconds * (self.value / 100))
            self.stop_timer()
            logger.debug(f"PlaybackScale._move_button_horizontal: Button moved horizontally. Current time set to {self.curr_time.miliseconds}ms.")

    def _on_button_release(self, event=None) -> None:
        """If there is an event, start the timer from the location, set the playback location to there and continue the animation."""
        if event:
            self.curr_time.miliseconds = int(self.end_time.miliseconds * (self.value / 100)) - 1
            self.spotify.set_playback_state_ms(self.curr_time.miliseconds)
            self.start_timer()
            self._start_animation_playback_position()
            logger.debug(f"PlaybackScale._on_button_release: Button released. Playback set to {self.curr_time.miliseconds}ms.")
    
    def _start_animation_playback_position(self) -> None:
        """Smoothly animate playback slider based on song duration."""
        current_time = self.curr_time.miliseconds
        total_duration = self.end_time.miliseconds
        self._move_playback_slider(current_time, total_duration)

        if current_time < total_duration:
            self._animation_id = self.after(1000, self._start_animation_playback_position)
            logger.debug("PlaybackScale._start_animation_playback_position: Starting animation for playback position.")

    def _move_playback_slider(self, current_time: int, total_duration: int) -> None:
        """Calculate and move the slider position based on playback progress."""
        progress = (current_time / total_duration) * 100 if total_duration > 0 else 0
        self.value = min(100, max(0, progress))
        logger.debug(f"PlaybackScale._move_playback_slider: Slider moved. Playback progress: {progress}%.")
        
    def _stop_animation(self) -> None:
        """Stops the animation of the playback slider and any ongoing timers."""
        if self._animation_id is not None:
            self.after_cancel(self._animation_id)
            self._animation_id = None
            logger.debug("PlaybackScale._stop_animation: Playback animation stopped.")
            
    