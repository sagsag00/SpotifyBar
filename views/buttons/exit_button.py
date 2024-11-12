from .custom_button import CustomButton
import os
import signal

class ExitButton(CustomButton):
    def __init__(self, master = None, **kwargs) -> None:
        super().__init__(master, "resources/buttons/exit.png", **kwargs)
        self.master = master
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_click(self):
        self.master.destroy()
        pid = os.getpid()  
        os.kill(pid, signal.SIGINT) 
        
    def on_enter(self, event):
        self.config(bg="#cf3c3c")
        
    def on_leave(self, event):
        self.config(bg=self.master.cget("bg"))