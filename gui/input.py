# Copyright 2026 Sagi Tsafrir

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from pathlib import Path
from tkinter import Label, Frame, Entry
import webbrowser

from gui.base import Base

class EnvInput(Base):
    def __init__(self,
                 title: str,
                 icon_path: str,
                 opacity: float = 1,
                 background_color: str = "lightgray") -> None:
        super().__init__(title, icon_path, opacity, background_color)
       

    def _setup(self) -> None:
        super()._setup(geometry=(500, 200))
        self.__load_widgets()

    def __load_widgets(self) -> None:
        parent_bg = self._window["bg"]
        lighter_bg = "#f0f0f0"
        common_font = ("TkDefaultFont", 10)

        msg = ("Opening Spotify for developers on your browser.\n"
               "Please create an app as stated in the README.md and provide\n"
               "the Client ID and Client Secret here.")
        Label(
            self._window,
            text=msg,
            justify="left",
            wraplength=480,
            bg=parent_bg,
            fg="#000000",
            font=("TkDefaultFont", 11)
        ).pack(pady=(10, 10))

        frame_id = Frame(self._window, bg=parent_bg)
        frame_id.pack(pady=(5, 5), padx=10, fill="x")
        Label(
            frame_id,
            text="Client ID:",
            width=15,
            anchor="w",
            bg=parent_bg,
            fg="#000000",
            font=("TkDefaultFont", 10, "bold")
        ).pack(side="left")
        self.client_id_entry = Entry(
            frame_id,
            width=40,
            bg=lighter_bg,
            bd=0,
            highlightthickness=0,
            font=common_font
        )
        self.client_id_entry.pack(side="left", fill="x", padx=(0, 5))

        frame_secret = Frame(self._window, bg=parent_bg)
        frame_secret.pack(pady=(5, 10), padx=10, fill="x")
        Label(
            frame_secret,
            text="Client Secret:",
            width=15,
            anchor="w",
            bg=parent_bg,
            fg="#000000",
            font=("TkDefaultFont", 10, "bold")
        ).pack(side="left")
        self.client_secret_entry = Entry(
            frame_secret,
            width=40,
            show="*",
            bg=lighter_bg,
            bd=0,
            highlightthickness=0,
            font=common_font
        )
        self.client_secret_entry.pack(side="left", fill="x", padx=(0, 5))

        submit_frame = Frame(self._window, bg=parent_bg)
        submit_frame.pack(fill="x", padx=10, pady=(0, 10))

        submit_button = Label(
            submit_frame,
            text="Submit",
            bg=lighter_bg,
            fg="#000000",
            font=common_font,
            padx=10,
            pady=4,
            cursor="hand2"
        )
        submit_button.pack(side="right")
        submit_button.bind("<Button-1>", lambda e: self.__on_submit())
        
        webbrowser.open("https://developer.spotify.com/dashboard")

    def __on_submit(self) -> None:
        client_id = self.client_id_entry.get().strip()
        client_secret = self.client_secret_entry.get().strip()

        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parent.parent

        env_file = base_dir / ".env"

        if not env_file.exists():
            env_file.write_text("CLIENT_ID=\nCLIENT_SECRET=\nREFRESH_TOKEN=\n")

        lines = env_file.read_text().splitlines()

        new_lines = []
        for line in lines:
            if line.startswith("CLIENT_ID="):
                new_lines.append(f"CLIENT_ID={client_id}")
            elif line.startswith("CLIENT_SECRET="):
                new_lines.append(f"CLIENT_SECRET={client_secret}")
            else:
                new_lines.append(line)

        env_file.write_text("\n".join(new_lines) + "\n")

        self._window.after(0, self._window.destroy)