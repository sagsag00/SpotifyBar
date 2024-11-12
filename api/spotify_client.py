import requests
import threading
from logger import logger

REPEAT_OFF = "off"
REPEAT_CONTEXT = "context"
REPEAT_TRACK = "track"


class SpotifyClient():
    """The backend client of spotify."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        del cls._instance
        cls._instance = super(SpotifyClient, cls).__new__(cls)
                
        return cls._instance
    
    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        
    def play(self) -> bool:
        """Lets you start/resume playback.

        Returns:
            bool: Returns whether or not it succeeded.
        """
        active_device_id = self.get_active_device_id()
        if not active_device_id:
            logger.warning("spotify_client.play: No available device found.")
            with open("api/info.ini", "r") as file:
                lines = file.readlines()
            for line in lines:
                if "device_id" not in line:
                    continue
                device_id = line.split("=")[1]
                self.transfer_playback(device_id)
                break

        url = "https://api.spotify.com/v1/me/player/play"
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
        return response.ok
        
    def pause(self) -> bool:
        """Lets you pause playback.

        Returns:
            bool: Returns whether or not it succeeded.
        """
        url = "https://api.spotify.com/v1/me/player/pause"
        
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
        
        return response.ok
    
    def is_player_active(self) -> bool | None:
        url = "https://api.spotify.com/v1/me/player"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        )

        if not response.text.strip():
            return None
            
        data = response.json()
        if data and 'is_playing' in data:
            return True if data['is_playing'] else False
        return None
    
    def is_shuffle_active(self) -> bool | None:
        url = "https://api.spotify.com/v1/me/player"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        )

        if not response.text.strip():
            return None
        
        data = response.json()
        if data and 'shuffle_state' in data:
            return True if data['shuffle_state'] else False
        return None
    
    def get_repeat_mode(self) -> str | None:
        """Gets the current active devices' repeat mode. 

            returns: str | None : `off`, `context`, `track`. None if no active device found.
        """
        url = "https://api.spotify.com/v1/me/player"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        )
        
        if not response.text.strip():
            return None

        data = response.json()
        if data and 'repeat_state' in data:
            repeat_mode = data['repeat_state']
            if repeat_mode == "off":
                return "off"
            elif repeat_mode == "context":
                return "context"
            elif repeat_mode == "track":
                return "track"
        return None
    
    def skip_to_next(self) -> bool:
        """Lets you skip to the next song in queue.

        Returns:
            bool: Returns whether or not it succeeded.
        """
        
        url = "https://api.spotify.com/v1/me/player/next"
        
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
    
        return response.ok
    
    def skip_to_previous(self) -> bool:
        """Lets you skip to the previous song played (queue exculded).

        Returns:
            bool: Returns whether or not it succeeded.
        """
        
        url = "https://api.spotify.com/v1/me/player/previous"
        
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
    
        return response.ok
    
    def set_repeat_mode(self, repeat: str) -> bool:
        """Sets the repeat mode for playback.

        Args:
            repeat (str): The repeat mode to set. Must be one of
                        `REPEAT_OFF`, `REPEAT_CONTEXT` or `REPEAT_TRACK`.

        Returns:
            bool: Returns whether or not it succeeded.
        """
        
        if repeat not in (REPEAT_OFF, REPEAT_CONTEXT, REPEAT_TRACK):
            raise ValueError(f"Invalid repeat mode: {repeat}. Must be one of: {REPEAT_OFF}, {REPEAT_CONTEXT}, {REPEAT_TRACK}")

        url = "https://api.spotify.com/v1/me/player/repeat"
    
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            },
            params={"state": repeat}
        )
        
        return response.ok
    
    def set_shuffle_mode(self, shuffle: bool) -> bool:
        """Sets the shuffle mode for playback.

        Args:
            shuffle (bool): The shuffle mode to set. True for shuffle on, False for shuffle off.

        Returns:
            bool: Returns whether or not it succeeded.
        """

        url = "https://api.spotify.com/v1/me/player/shuffle"
        
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            },
            params={"state": str(shuffle).lower()}  # Spotify API expects 'true' or 'false' as string
        )
        
        return response.ok

    def get_playback_state_ms(self) -> int | None:
        """Gets the playback state in ms.

        Returns:
            int: Returns the playback state in miliseconds.
        """
        
        url = "https://api.spotify.com/v1/me/player"
        
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
    
        if not response.text.strip():
            return None
        
        response_json = response.json()
        
        return response_json["progress_ms"]
    
    def get_song_length_ms(self) -> int | None:
        """Gets the total song length in milliseconds.

        Returns:
            int: Returns the song length in milliseconds, or None if unavailable.
        """
        url = "https://api.spotify.com/v1/me/player"
        
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )

        if not response.text.strip():
            return None
        
        response_json = response.json()
        
        if "item" in response_json and response_json["item"] is not None:
            return response_json["item"]["duration_ms"]
        
        return None
    
    def set_playback_state_ms(self, ms: int) -> bool:
        """Sets the playback state with miliseconds.
            Returns:
                bool: Returns whether or not the the playback was set successfully. True if it was, False otherwise.
        """
        url = "https://api.spotify.com/v1/me/player/seek"
    
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            },
            params={"position_ms": ms}
        )
        
        return response.ok
        
    def get_current_playing_track(self) -> dict:
        """Gets the current playing tracks data.

        Returns:
            dict: The json with all of the tracks data.
        """
        
        url = "https://api.spotify.com/v1/me/player/currently-playing"
        
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
    
        if not response.text.strip():
            return None
        
        response_json = response.json()
        
        return response_json
        
    
    def get_song_title(self) -> str:
        """Gets the current playing song title.

        Returns:
            str: Returns the current songs name.
        """
        track = self.get_current_playing_track()
        
        if not track:
            return None
        
        if not track.get("item", None):
            return "Unknown"
        
        return track["item"]["name"] 
        
    def get_song_artist(self) -> str:
        """Gets the current playing song artist.

        Returns:
            str: Returns the current songs artist.
        """    
        track = self.get_current_playing_track()
        
        if not track:
            return None
        
        return track["item"]["artists"][0]["name"]
    
    def get_song_album(self) -> str:
        """Gets the current playing songs album.

        Returns:
            str: Returns the current songs album.
        """
        track = self.get_current_playing_track()
        
        if not track:
            return None
        
        return track["item"]["album"]["name"]
    
    def get_volume(self) -> int | None:
        """Gets the current volume level (0 to 100).

        Returns:
            int: Returns the current volume level in percentage, or None if unavailable.
        """
        url = "https://api.spotify.com/v1/me/player"
        
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
        )
        
        if not response.text.strip():
            return None
        
        response_json = response.json()
        
        if "device" in response_json and response_json["device"] is not None:
            return response_json["device"].get("volume_percent")
        
        return None
    
    def set_volume(self, volume: int) -> bool:
        """Sets the volume level for playback.

        Args:
            volume (int): The volume level to set. Must be between 0 and 100.

        Returns:
            bool: Returns whether or not the request succeeded.
        """
        if not (0 <= volume <= 100):
            raise ValueError("Volume must be between 0 and 100.")
        
        active_device_id = self.get_active_device_id()
        if not active_device_id:
            logger.warning("spotify_client.set_volume: No available device found.")
            with open("api/info.ini", "r") as file:
                lines = file.readlines()
            for line in lines:
                if "device_id" not in line:
                    continue
                device_id = line.split("=")[1]
                self.transfer_volume(volume, device_id)
                break
        
        url = "https://api.spotify.com/v1/me/player/volume"
        
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            },
            params={"volume_percent": volume}
        )
        
        return response.ok
    
    def transfer_volume(self, volume: int, device_id: str) -> bool:
        """Sets the playback volume on the specified device.
        
        Args:
            volume (int): The desired volume level (0-100).
            device_id (str): The ID of the target device.

        Returns:
            bool: Returns whether or not the request succeeded.
        """
        if not (0 <= volume <= 100):
            raise ValueError("Volume must be between 0 and 100.")
        
        url = "https://api.spotify.com/v1/me/player/volume"
        params = {"volume_percent": volume}
        json_data = {"device_ids": [device_id]}
        
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            },
            params=params,
            json=json_data
        )
        return response.ok

    
    def get_active_device_id(self) -> str | None:
        """Returns the active device ID if active, None otherwise."""
        url = "https://api.spotify.com/v1/me/player/devices"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        )

        if not response.ok:
            return None

        devices = response.json().get("devices", [])
        for device in devices:
            if device.get("is_active"):
                with open("api/info.ini", "w+") as file:
                    lines = file.readlines()
                    if not lines:
                        lines = []
                    if not "device_id" in lines:
                        lines.append(f"device_id={device.get("id")}") 
                    file.writelines(lines)                   
                return device.get("id")
        return None

    def transfer_playback(self, device_id: str) -> bool:
        """Starts the playback of the device id. 
        
            Returns:
                bool: Returns whether or not the request succeeded.
        """
        url = "https://api.spotify.com/v1/me/player"
        response = requests.put(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            },
            json={"device_ids": [device_id], "play": False}
        )
        return response.ok

    def get_cover_url(self) -> str | None:
        """Gets the album image URL of the currently playing track.

        Returns:
            str: URL of the album image, or None if unavailable.
        """
        track = self.get_current_playing_track()
        if not track:
            return None
        
        # Check if the 'album' field and 'images' are available.
        album = track.get("item", {}).get("album", {})
        images = album.get("images", [])
        if images:
            # Return the last image (usually the lowest resolution).
            return images[0].get("url")
        return None

    def get_queue(self) -> list | None:
        """Gets the current playback queue.

        Returns:
            list: A list of track information dictionaries in the queue, or None if unavailable.
        """
        url = "https://api.spotify.com/v1/me/player/queue"
        
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        )
        
        if not response.text.strip():
            return None
        
        queue_data = response.json()
        
        # The 'queue' field contains the list of tracks in the playback queue.
        return queue_data.get("queue", [])
    
    def get_recently_played(self, limit=20) -> list | None:
        """Gets a list of recently played tracks.

        Args:
            limit (int): Number of tracks to retrieve, with a max of 50.

        Returns:
            list: A list of dictionaries with metadata for each recently played track, or None if unavailable.
        """
        url = f"https://api.spotify.com/v1/me/player/recently-played?limit={limit}"
        
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}"
            }
        )
        
        if not response.text.strip():
            return None
        
        return response.json().get("items", [])
    
    def get_artist_uri(self) -> str | None:
        """Gets the Spotify URI of the primary artist of the currently playing track.

        Returns:
            str: The Spotify URI of the primary artist, or None if unavailable.
        """
        track = self.get_current_playing_track()
        
        if not track:
            return None

        artist_id = track["item"]["artists"][0]["id"]
        return f"spotify:artist:{artist_id}"

    def get_album_uri(self) -> str | None:
        """Gets the URI of the current playing song's album.

        Returns:
            str: The URI of the current song's album.
        """
        track = self.get_current_playing_track()
        
        if not track:
            return None
        
        return track["item"]["album"]["uri"]
