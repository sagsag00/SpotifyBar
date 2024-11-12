from tkinter import Button, Tk, PhotoImage
from PIL import Image, ImageTk
from api import Spotify

class CustomButton(Button):
    def __init__(self, master: Tk = None, image_path: str = None, **kwargs) -> None:
        if kwargs.get("text"):
            kwargs["text"] = None
            
        kwargs["command"] = self.on_click
        kwargs["borderwidth"] = 0
        kwargs["relief"] = "flat"
        kwargs["background"] = master.cget("background")
        kwargs["activebackground"] = master.cget("background")
        kwargs["highlightbackground"] = master.cget("background")
        kwargs["width"] = kwargs.get("width", 2)
        kwargs["height"] = kwargs.get("height", 1)
        
        self.tk_image = None
        
        super().__init__(master, **kwargs)
        
        if image_path:
            self.tk_image = self.add_image(image_path)
            self.config(image=self.tk_image, width=24, height=20)
        
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        self.spotify = Spotify()

    def on_press(self, event):
        """On press make the button a bit smaller (animation)."""
        self.config(width=22, height=18)

    def on_release(self, event):
        """On release return the button to its' original size (animation)."""
        self.config(width=24, height=20)
       
    def add_image(self, image_path: str) -> ImageTk.PhotoImage:
        """Adds an image to the button"""
        image = Image.open(image_path)
        image.thumbnail((15, 15))
        self.tk_image = ImageTk.PhotoImage(image)
        
        return self.tk_image
        
    def on_click(self):
        """On click function. Has to implement on each button"""
        raise NotImplementedError("function on_click is not defined.")