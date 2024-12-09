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

from views.scales import Scale
from logger import logger

class VolumeScale(Scale):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, "vertical", **kwargs)
        self.bind("<B1-Motion>", self._move_button_vertical)
    
        self._volume_update_job = None
        logger.debug(f"VolumeScale.__init__: VolumeScale initialized with master={master} and kwargs={kwargs}")
        
    def load(self):
        self.value = self.spotify.get_volume()
        logger.debug(f"VolumeScale.load: VolumeScale loaded with initial volume={self.value}")
        
    def _move_button_vertical(self, event=None) -> None:
        logger.debug(f"VolumeScale._move_button_vertical: Volume scale moved with event={event}")
        super()._move_button_vertical(event)
        
        if self._volume_update_job:
            self.after_cancel(self._volume_update_job)
            logger.debug(f"VolumeScale._move_button_vertical: Volume update job canceled")
        
        self._volume_update_job = self.after(200, self._update_volume)
        logger.debug(f"VolumeScale._move_button_vertical: Scheduled volume update in 200ms")

    def _update_volume(self):
        self.spotify.set_volume(self.value)
        self._volume_update_job = None
        logger.debug(f"VolumeScale._update_volume: Volume updated to {self.value}")
