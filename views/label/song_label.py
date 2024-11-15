from tkinter import Label
from api import Spotify
from typing import Callable
import threading
from logger import logger

SONG = 0
ARTIST = 1
ALBUM = 2

class SongLabel(Label):
    def __init__(self, master = None, font_size = 12, is_bold = True, max_width: int = 125, **kwargs):
        bold = ""
        if is_bold:
            bold = "bold"
        kwargs["fg"] = "black"
        kwargs["font"] = ("Circular-black", font_size, bold)
        kwargs["bg"] = master.cget("bg")
        super().__init__(master, **kwargs)

        self.max_width = max_width
        self.spotify = Spotify()
        self.callable: Callable = None
        
        self.bind("<Button-1>", lambda e: self.on_click())
        logger.debug(f"SongLabel.__init__: SongLabel initialized with font_size={font_size}, is_bold={is_bold}, max_width={max_width}")

        
    def set_callback(self, callable: Callable) -> None:
        self.callable = callable
        logger.debug("SongLabel.set_callback: Function has completed.") 
     
    def on_click(self):
        if self.callable:
            logger.info("SongLabel.on_click: On click triggered. Executing callable function.")
            threading.Thread(target=self.callable).start()
        else:
            logger.warning("SongLabel.on_click triggered, but no callable function is set.")
        logger.debug("SongLabel.on_click: Function has completed.") 
    
    def load(self, type: int) -> None:
        logger.debug(f"SongLabel.load: loading with type={type}")
        if type not in (SONG, ARTIST, ALBUM):
            logger.error(f"SongLabel.load: Invalid type {type} passed to load function.")
            return
        if type is SONG:
            return self.__load_song()
        if type is ARTIST:
            return self.__load_artist()
        return self.__load_album()
                
    def __load_song(self) -> None:
        self.title = self.spotify.get_song_title()
    
    def __load_artist(self) -> None:
        self.title = self.spotify.get_song_artist()
        
    def __load_album(self) -> None:
        self.title = f"- {self.spotify.get_song_album()}"

    @property
    def title(self) -> str:
        return self.cget("text")
    
    @title.setter
    def title(self, new_title: str) -> None:
        if not new_title or new_title.strip() == "- None":
            new_title = "Unknown"
            logger.info("SongLabel.title.setter: Title was empty or 'None', setting to 'Unknown'")
            
        truncated_title = new_title

        self.config(text=truncated_title)
        self.update_idletasks()

        while self.winfo_reqwidth() > self.max_width and len(truncated_title) > 1:
            truncated_title = truncated_title[:-2] + "…"
            self.config(text=truncated_title)
            self.update_idletasks()

        self.config(text=truncated_title)
        logger.debug(f"SongLabel.title.setter: Final title set: {truncated_title}")
