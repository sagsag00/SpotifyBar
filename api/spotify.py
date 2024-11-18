from .refresh import SpotifyAuth, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN
import time 
import subprocess
from .spotify_client import SpotifyClient
import threading
import webbrowser
from logger import logger
import os
    
class Spotify():
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Spotify, cls).__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """A class that controls Spotify."""
        if not hasattr(self, "initialized"):
            self.initialized = True
            token = self.refresh()
            self.spotify_client = SpotifyClient(token)
            threading.Thread(target=self.refresh_client, daemon=True).start()
            
        self.__volume = self.get_volume()
        if not self.__volume:
            self.__volume = 50
        
    def refresh(self) -> str:
        """Refreshes the clients' access token."""
        spotify_auth = SpotifyAuth(CLIENT_ID, CLIENT_SECRET)
        spotify_auth.run()
        return spotify_auth.refresh(REFRESH_TOKEN)
        
    def refresh_client(self) -> None:
        """Refreshes the SpotifyClient access token."""
        while True:
            time.sleep(3500)
            
            token = self.refresh()
            self.spotify_client = SpotifyClient(token)
            logger.info("Spotify.refresh_client: Client refreshed.")
        
    def open_spotify_app(self) -> bool:
        """Opens the spotify app.

        Returns:
            bool: Returns whether or not the app opened successfully. True if it did, False otherwise.
        """
        try:
            subprocess.Popen(
                ["start", "spotify:",],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True  # Necessary to use 'start' command
            )
            logger.info("Spotify.open_spotify_app: Spotify client opened.")
            return True
        except Exception as e:
            logger.warning(f"Spotify.open_spotify_app: Failed to open Spotify. Error: {e}")
            return False

    def play(self) -> bool:
        """Lets you start/resume playback."""
        return self.spotify_client.play()
    
    def pause(self) -> bool:
        """Lets you pause playback."""
        return self.spotify_client.pause()
    
    def is_player_active(self) -> bool | None:
        """Returns whether or not the player is active. If player not found will return None."""
        return self.spotify_client.is_player_active()
    
    def is_shuffle_active(self) -> bool | None:
        """Returns whether or not the shuffle is active. If shuffle not found will return None."""
        return self.spotify_client.is_shuffle_active()
    
    def get_repeat_mode(self) -> str | None:
        """Returns the active repeat mode. If repeat not found will return None."""
        return self.spotify_client.get_repeat_mode()
    
    def skip_to_next(self) -> bool:
        """Lets you skip to the next song in queue."""
        return self.spotify_client.skip_to_next()
    
    def skip_to_previous(self) -> bool:
        """Lets you skip to the previous song played (queue excluded)."""
        return self.spotify_client.skip_to_previous()
    
    def set_repeat_mode(self, repeat: str) -> bool:
        """Sets the repeat mode for playback."""
        return self.spotify_client.set_repeat_mode(repeat)
    
    def set_shuffle_mode(self, shuffle: str) -> bool:
        """Sets the shuffle mode for playback."""
        if shuffle.lower() == "on":
            return self.spotify_client.set_shuffle_mode(True)
        elif shuffle.lower() == "off":  
            return self.spotify_client.set_shuffle_mode(False)
        return False
    
    def get_playback_state_ms(self) -> int | None:
        """Gets the playback state in milliseconds."""
        return self.spotify_client.get_playback_state_ms()
    
    def get_playback_state_seconds(self) -> int | None:
        """Gets the playback state in seconds (floor round)."""
        ms = self.get_playback_state_ms()
        if ms:
            return  ms // 1000 
        return None
    
    def get_playback_state_minutes(self) -> int | None:
        """Gets the playback state in minutes (floor round)."""
        seconds = self.get_playback_state_seconds()
        if seconds:
            return  seconds // 60 
        return None
    
    def get_playback_state_timer(self) -> str | None:
        """Gets the playback state in this format: "xx:xx"."""
        seconds = self.get_playback_state_seconds()
        minutes = self.get_playback_state_minutes()
        if seconds is None or minutes is None:
            return None
        seconds -= minutes * 60
        return f"{minutes}:{seconds:02}"
    
    def set_playback_state_ms(self, ms: int) -> bool:
        """Sets the playback state with miliseconds.
            Returns:
                bool: Returns whether or not the the playback was set successfully. True if it was, False otherwise.
        """
        return self.spotify_client.set_playback_state_ms(ms)
        
    def set_playback_state_seconds(self, sec: int) -> bool:
        """Sets the playback state with seconds.
            Returns:
                bool: Returns whether or not the the playback was set successfully. True if it was, False otherwise.
        """
        return self.set_playback_state_ms(sec * 1000)
    
    def get_song_duration_ms(self) -> int | None:
        """Gets the song duration in milliseconds."""
        return self.spotify_client.get_song_length_ms()  # Assuming you have this method defined in spotify_client

    def get_song_duration_seconds(self) -> int | None:
        """Gets the song duration in seconds (floor round)."""
        ms = self.get_song_duration_ms()
        if ms is not None:
            return ms // 1000
        return None

    def get_song_duration_minutes(self) -> int | None:
        """Gets the song duration in minutes (floor round)."""
        seconds = self.get_song_duration_seconds()
        if seconds is not None:
            return seconds // 60
        return None

    def get_song_duration_timer(self) -> str | None:
        """Gets the song duration in this format: "xx:xx"."""
        seconds = self.get_song_duration_seconds()
        minutes = self.get_song_duration_minutes()

        if seconds is not None and minutes is not None:
            seconds = seconds % 60  # Remaining seconds after converting to minutes
            return f"{minutes}:{seconds:02}"
        
        return None

    def get_current_playing_track(self) -> dict | None:
        """Gets the current playing tracks data.

        Returns:
            dict: The json with all of the tracks data.
        """
        
        return self.spotify_client.get_current_playing_track()

    def get_song_title(self) -> str | None:
        """Returns the current playing songs' title"""
        return self.spotify_client.get_song_title()
    
    def get_song_artist(self) -> str | None:
        """Returns the current playing songs' artist"""
        return self.spotify_client.get_song_artist()
    
    def get_song_album(self) -> str | None:
        """Returns the current playing songs' album"""
        return self.spotify_client.get_song_album()
    
    def get_volume(self) -> int | None:
        """Gets the volume of the current playing device"""
        return self.spotify_client.get_volume()
    
    def set_volume(self, volume: int) -> bool:
        """Sets the volume of the current playing device"""
        self.__volume = self.spotify_client.set_volume(volume)
        return self.__volume
        
    def get_cover_url(self) -> str:
        """Gets the cover_url of the current playing track"""
        return self.spotify_client.get_cover_url()
    
    def get_queue(self) -> list:
        """Gets the queue of the current playing device"""
        return self.spotify_client.get_queue()
    
    def get_recently_played(self, limit = 20) -> list | None:
        """Gets the recently played of the current playing device"""
        return self.spotify_client.get_recently_played(limit)
    
    def get_artist_uri(self) -> str | None:
        """Gets the artists' uri of the current playing tracks' artist"""
        return self.spotify_client.get_artist_uri()
    
    def get_album_uri(self) -> str | None:
        """Gets the albums' uri of the current playing tracks' album"""
        return self.spotify_client.get_album_uri()
    
    def open_uri_in_spotify(self, uri: str) -> None:
        """Opens the uri's page in the Spotify app, if available."""
        
        if uri:
            webbrowser.open(uri)
        else:
            logger.warning("spotify.open_uri_in_spotify: No URI available to open.")
    
    @property
    def volume(self) -> int:
        return self.__volume
    
        
if __name__ == "__main__":
    spotify = Spotify()
    
    logger.debug(f"{spotify.get_volume()=}")
    spotify.set_volume(0)