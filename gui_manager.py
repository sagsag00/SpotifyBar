from views.scales import PlaybackScale, VolumeScale
from views.buttons import ExitButton, NextButton, PreviousButton, PauseButton, RepeatButton, ShuffleButton
from views.label import SongLabel, TimeLabel
import threading
from api import Spotify
from tkinter import Label, PhotoImage
from PIL import Image, ImageTk
import requests
from io import BytesIO
import time
from logger import logger

class GuiManager():
    """Manages the given views."""
    
    def __init__(self, master, **kwargs) -> None:
        """Manages the given views.

        Possible arguements:
            exit_button, next_button, previous_button, pause_button, repeat_button, shuffle_buttln,
            song_label, artist_label, album_label, time_label, playback_scale, volume_scale, song_pic
        """
        
        self.master = master
        self.views = {}
        self.spotify = Spotify()
        
        self.skip_count = 0
        self.last_skip_time = 0
        self.skip_reset_duration = 1
        self.skipping = False
        self.finished_song = False
        self._check_song_thread_id = None
        self._check_pause_thread_id = None
        
        allowed_keys = {
            "exit_button", "next_button", "previous_button", "pause_button", "repeat_button",
            "shuffle_button", "song_label", "artist_label", "album_label", "time_label",
            "playback_scale", "volume_scale", "song_pic"
        }

        for key, value in kwargs.items():
            if key in allowed_keys:
                setattr(self, key, value)
                self.views[key] = value
            else:
                logger.warning(f"GuiManager.__init__: '{key}' is not a recognized argument and will be ignored.")
        
    def load_all(self) -> None:
        """Load all of the given views."""
        logger.info("GuiManager.load_all: Loading all views...")
        
        if hasattr(self, "playback_scale") and isinstance(self.playback_scale, PlaybackScale):
            self.playback_scale.set_stop_callback(self.on_playback_scale_next)
            self.playback_scale.load()
            logger.debug("GuiManager.load_all: Playback scale loaded.")

        if hasattr(self, "volume_scale") and isinstance(self.volume_scale, VolumeScale):
            self.volume_scale.load()
            logger.debug("GuiManager.load_all: Volume scale loaded.")

        if hasattr(self, "next_button") and isinstance(self.next_button, NextButton):
            self.next_button.set_callable(self.on_next_button_click)
            logger.debug("GuiManager.load_all: Next button loaded.")

        if hasattr(self, "previous_button") and isinstance(self.previous_button, PreviousButton):
            self.previous_button.set_callable(self.on_previous_button_click)
            logger.debug("GuiManager.load_all: Previous button loaded.")

        if hasattr(self, "pause_button") and isinstance(self.pause_button, PauseButton):
            self.pause_button.set_callback(self.on_pause_button_click)
            self.pause_button.load()
            logger.debug("GuiManager.load_all: Pause button loaded.")
            
            if self.pause_button.is_playback_active() and hasattr(self, "playback_scale") and isinstance(self.playback_scale, PlaybackScale):
                self.playback_scale.start()

        if hasattr(self, "shuffle_button") and isinstance(self.shuffle_button, ShuffleButton):
            self.shuffle_button.load()
            logger.debug("GuiManager.load_all: Shuffle button loaded.")

        if hasattr(self, "repeat_button") and isinstance(self.repeat_button, RepeatButton):
            self.repeat_button.load()
            logger.debug("GuiManager.load_all: Repeat button loaded.")

        if hasattr(self, "song_label") and isinstance(self.song_label, SongLabel):
            self.song_label.load(type=0)
            logger.debug("GuiManager.load_all: Song label loaded.")
            
            if self.song_label.title == "Unknown":
                volume = self.spotify.volume 
                self.spotify.set_volume(5)
                self.spotify.play()
                self.spotify.pause()
                self.spotify.set_volume(volume)
                self.load_all()

        if hasattr(self, "artist_label") and isinstance(self.artist_label, SongLabel):
            self.artist_label.set_callable(self.on_button_click_artist)
            self.artist_label.load(type=1)
            logger.debug("GuiManager.load_all: Artist label loaded.")

        if hasattr(self, "album_label") and isinstance(self.album_label, SongLabel):
            self.album_label.set_callable(self.on_button_click_album)
            self.__load_album_label()
            logger.debug("GuiManager.load_all: Album label loaded.")

        if hasattr(self, "song_pic") and isinstance(self.song_pic, Label):
            self.__load_song_image()
            logger.debug("GuiManager.load_all: Song picture loaded.")

        logger.debug("GuiManager.load_all: Function has completed.")
        
        if self._check_song_thread_id is None:
            threading.Thread(target=self.__check_for_changes_song).start()
            logger.debug("GuiManager.load_all: Started background thread to check for changes.")
        if self._check_pause_thread_id is None:
            threading.Thread(target=self.__check_for_changes_pause).start()
            logger.debug("GuiManager.load_all: Started background thread to check for changes.")
                    
    def on_playback_scale_next(self):
        """Callback function executed when playback_scale calls stop_timer."""
        logger.info("GuiManager.on_playback_scale_next: Playback scale next callback triggered.")
        
        self.finished_song = True
        
        if not self.pause_button.is_active:
            self.pause_button.is_active = False
            self.pause_button.change_image()
        
        self.skip_count = 1
        threading.Thread(target=self.__load_next_track_details).start()
        
        logger.debug("GuiManager.on_playback_scale_next: Function has completed.")
        
    def on_pause_button_click(self, is_paused: bool):
        """Callback function executed when the pause button is clicked."""
        logger.debug(f"GuiManager.on_pause_button_click: Pause button clicked. Paused: {is_paused}")
        
        self.playback_scale.load()
        if is_paused:
            self.playback_scale.stop_timer()
            self.playback_scale.load()
            return
        self.playback_scale.start_timer()
        self.playback_scale.load()
        self.playback_scale._start_animation_playback_position()
        
        logger.debug("GuiManager.on_pause_button_click: Function has completed.")
        
    def on_previous_button_click(self):
        """Callback function executed when the previous button is clicked."""
        logger.debug("GuiManager.on_previous_button_click: Previous button clicked.")
        
        if self.playback_scale.value > 5:
            self.playback_scale.reset()
            self.spotify.set_playback_state_ms(0)
            return
        
        self.playback_scale.reset()
        self.spotify.skip_to_previous()
        time.sleep(1)
        self.__current_track_load_views()
        
        logger.debug("GuiManager.on_previous_button_click: Function has completed.")
        
    def on_next_button_click(self):
        """Callback function for when the next button is clicked."""
        logger.debug("GuiManager.on_next_button_click: Next button clicked.")
        current_time = time.time()

        if current_time - self.last_skip_time > self.skip_reset_duration:
            self.skip_count = 1
        else:
            self.skip_count += 1

        self.last_skip_time = current_time

        if not self.pause_button.is_active:
            self.pause_button.is_active = True

        threading.Thread(target=self.__skip_to_next).start()
        threading.Thread(target=self.__load_next_track_details).start()
               
        logger.debug("GuiManager.on_next_button_click: Function has completed.")
        
    def on_button_click_artist(self) -> None:
        """Callback function for when the artist button is clicked.
            The function opens the current playing tracks' artist in the spotify app
        """
        logger.info("GuiManager.on_button_click_artist: Artist button clicked.")
        if not self.spotify.open_spotify_app():
            logger.error("GuiManager.on_button_click_artist: Spotify app could not open")
        
        self.spotify.open_uri_in_spotify(self.spotify.get_artist_uri())
    
    def on_button_click_album(self) -> None:
        """Callback function for when the album button is clicked.
            The function opens the current playing tracks' album in the spotify app
        """
        logger.info("Album button clicked.")
        if not self.spotify.open_spotify_app():
            logger.error("GuiManager.on_button_click_artist: Spotify app could not open")
        
        self.spotify.open_uri_in_spotify(self.spotify.get_album_uri())
       
    def __check_for_changes_song(self) -> None:
        """Checks for changes in the Spotify app of the track itself. 
        (Meaning if the song was changed in Spotify, the app will register the change)"""
        logger.info("GuiManager.__check_for_changes_song: Started checking for song changes.")
        self._check_song_thread_id = "_check_thread"
        
        while True:
            if self.skipping or self.finished_song:
                self.finished_song = False
                time.sleep(10)
                continue
            
            if self.song_label.title[:10] != self.spotify.get_song_title()[:10]:
                self.__current_track_load_views()
                self.playback_scale.load()
            
            time.sleep(1) 
            
    def __check_for_changes_pause(self) -> None:
        """Checks for changes in the Spotify app of the pause button. 
        (Meaning if the song was paused in Spotify, the app will register the pause)"""
        logger.info("GuiManager.__check_for_changes_pause: Started checking for pause changes.")
        self._check_pause_thread_id = "_check_thread"
        
        while True:
            if self.pause_button.is_active != self.spotify.is_player_active():
                threading.Thread(target=self.on_pause_button_click(self.pause_button.is_active))
                threading.Thread(target=self.pause_button.load())
            time.sleep(1)
    
    def __skip_to_next(self) -> None:
        """Skips to the next song(s), depands on self.skip_count"""
        logger.info("GuiManager.__skip_to_next: Skipping to next track.")
        self.skipping = True
        for _ in range(self.skip_count):
            self.spotify.skip_to_next()
            time.sleep(0.1)
        self.playback_scale.reset()
        
        self.skipping = False
        logger.debug(f"GuiManager.__skip_to_next: Total skips: {self.skip_count}")
        logger.debug(f"GuiManager.__skip_to_next: Function has completed.")

        
    def __load_next_track_details(self):
        """Loads the next track in queue details."""
        logger.info("GuiManager.__load_next_track_details: Loading next track details.")
        queue = self.spotify.get_queue()

        if self.skip_count <= len(queue):
            target_track = queue[self.skip_count - 1]
            self.song_label.title = target_track["name"]
            self.artist_label.title = target_track["artists"][0]["name"]
            self.__load_album_label(title=target_track["album"]["name"])
            self.__load_song_image(target_track["album"]["images"][0]["url"])

            self.playback_scale.reset()
            self.playback_scale.end_time.miliseconds = target_track["duration_ms"]

        logger.debug(f"GuiManager.__load_next_track_details: Function has completed.")

        
    def __current_track_load_views(self) -> None:
        """Loads the current track views"""
        logger.info("GuiManager.__current_track_load_views: Loading currents track views")
        
        self.song_label.load(type=0)
        self.artist_label.load(type=1)
        self.__load_album_label()
        self.__load_song_image()
        
        logger.debug(f"GuiManager.__current_track_load_views: Function has completed.")
        
    def __load_album_label(self, title: str = None) -> None:
        """Loads the album's label. Takes into account the artist's label width to not overlap with volume bar.

        Args:
            title (str, optional): The title of the label. Defaults to None.
        """
        logger.debug("GuiManager.__load_album_label: Loading album label.")
        self.master.update_idletasks()
            
        artist_label_width = self.artist_label.winfo_width()
        
        self.album_label.place(x=self.artist_label.winfo_x() + artist_label_width, y=self.artist_label.winfo_y())
        self.album_label.max_width = 230 - artist_label_width
        if title:
            self.album_label.title = f"- {title}"
        else:
            self.album_label.load(type=2)
        
        logger.debug("GuiManager.__load_album_label: Function has completed.")

    def __load_song_image(self, image_url: str = None) -> None:
        """Fetch and update the song image in the song_pic label."""
        logger.debug("GuiManager.__load_song_image: Loading the currents tracks' image.")
        if not image_url:
            image_url = self.spotify.get_cover_url()
        
        try:
            response = requests.get(image_url)
            img_data = response.content
            image = Image.open(BytesIO(img_data))
            
            # Get a fixed size for the image (could be the label's initial size or a max size you want)
            fixed_width = 83  
            fixed_height = 83 
            
            image = self._resize_image_maintaining_aspect_ratio(image, fixed_width, fixed_height)
            
            photo = ImageTk.PhotoImage(image)
            
            self.song_pic.config(image=photo)
            self.song_pic.image = photo  # Keep a reference to the image to prevent garbage collection
            
        except Exception as e:
            logger.error(f"GuiManager.__load_song_image: Error loading song image: {e}")
            
        logger.debug("GuiManager.__load_song_image: Function has completed.")
            
    def _resize_image_maintaining_aspect_ratio(self, image: PhotoImage, max_width: int, max_height: int) -> PhotoImage:
        """Resize the image while maintaining its aspect ratio."""
        logger.debug("GuiManager._resize_image_maintaining_aspect_ratio: Resizing the image.")
        img_width, img_height = image.size
        aspect_ratio = img_width / img_height
        
        if img_width > max_width or img_height > max_height:
            if img_width / max_width > img_height / max_height:
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        logger.debug("GuiManager._resize_image_maintaining_aspect_ratio: Function has completed.")
        return image
    