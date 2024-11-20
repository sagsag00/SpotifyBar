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