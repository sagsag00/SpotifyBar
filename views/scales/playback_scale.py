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
        
    def convert_time_to_value(self):
        raise NotImplementedError
    
    def start(self):
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
        """Starts the timer and updates every second."""
        self.curr_time.seconds += 1
        if self.curr_time.seconds >= 60:
            self.curr_time.seconds = 0
            self.curr_time.minutes += 1
            
        if self.curr_time.seconds % 20 == 0 and self.curr_time.seconds != 0:
            self.load()
            self.load()
            self.load()

        delay = time_difference_ms if not hasattr(self, "_timer_id") else 1000
        
        if self.curr_time + 1 >= self.end_time:
            self.stop_timer()
            self.stop_callback()
            logger.debug("PlaybackScale.start_timer: End time reached, stopping playback.")
            return
        
        self._timer_id = self.after(delay, self.start_timer)
        logger.debug(f"PlaybackScale.start_timer: Timer started with delay: {delay}ms.")

    def stop_timer(self) -> None:
        """Stops the timer."""
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None 
            logger.debug("PlaybackScale.stop_timer: Timer stopped.")
            
    def reset(self) -> None:
        self.stop_timer()
        self.curr_time.curr_time = "00:00"
        self.start_timer()
        self._start_animation_playback_position()
        
        logger.debug("PlaybackScale.reset: PlaybackScale reset.")
            
    def load(self):
        self.curr_time.curr_time = self.spotify.get_playback_state_timer()
        self.end_time.curr_time = self.spotify.get_song_duration_timer()
        self.value = (self.curr_time.miliseconds / (self.end_time.miliseconds + 0.1)) * 100
        logger.debug(f"PlaybackScale.load: Loaded current time: {self.curr_time.curr_time}, end time: {self.end_time.curr_time}.")
        
    def _move_button_horizontal(self, event=None) -> None:
        super()._move_button_horizontal(event)

        if event:
            self.curr_time.miliseconds = int(self.end_time.miliseconds * (self.value / 100))
            self.stop_timer()
            self._stop_animation()
            logger.debug(f"PlaybackScale._move_button_horizontal: Button moved horizontally. Current time set to {self.curr_time.miliseconds}ms.")

    def _on_button_release(self, event=None) -> None:
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
            
    