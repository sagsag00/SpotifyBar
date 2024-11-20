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

from tkinter import Label
from logger import logger

class TimeLabel(Label):
    def __init__(self, master = None, start_time: str = "00:00", **kwargs) -> None:
        kwargs["text"] = start_time 
        super().__init__(master, **kwargs)
        
        self.__curr_time_min = int(start_time.split(":")[0])
        self.__curr_time_sec = int(start_time.split(":")[1])
        
        logger.debug("TimeLabel.__init__: TimeLabel is initialized")
           
    @property
    def text(self) -> str:
        return self.cget("text")
    
    @text.setter
    def text(self, new_val: str) -> None:
        self.config(text=new_val)
        
    @text.deleter
    def text(self) -> None:
        self.config(text="00:00")
        
    @property
    def curr_time(self) -> str:
        return f"{self.__curr_time_min}:{self.__curr_time_sec}"
    
    @curr_time.setter
    def curr_time(self, new_value) -> None:
        if new_value is None:
            return
        self.__curr_time_min = int(new_value.split(":")[0])
        self.__curr_time_sec = int(new_value.split(":")[1])
        self.config(text=new_value)
    
    @curr_time.deleter
    def curr_time(self) -> None:
        self.__curr_time_min = 0
        self.__curr_time_sec = 0
        self.text = f"{self.minutes}:{self.seconds:02}"
    
    @property
    def minutes(self) -> int:
        return self.__curr_time_min
    
    @minutes.setter
    def minutes(self, new_value) -> None:
        if new_value is None:
            return
        self.__curr_time_min = new_value
        self.text = f"{self.minutes}:{self.seconds:02}"
    
    @minutes.deleter
    def minutes(self) -> None:
        self.__curr_time_min = 0
        self.text = f"{self.minutes}:{self.seconds:02}"
    
    @property
    def seconds(self) -> int:
        return self.__curr_time_sec
    
    @seconds.setter
    def seconds(self, new_value) -> None:
        if new_value is None:
            return
        if new_value >= 60:
            self.__curr_time_min += new_value // 60
        self.__curr_time_sec = new_value % 60
        self.text = f"{self.minutes}:{self.seconds:02}"
        
    @seconds.deleter
    def seconds(self) -> None:
        self.__curr_time_sec = 0
        self.text = f"{self.minutes}:{self.seconds:02}"
        
    @property
    def miliseconds(self) -> int:
        return (self.minutes * 60 + self.seconds) * 1000
    
    @miliseconds.setter
    def miliseconds(self, new_val: int) -> None:
        seconds = new_val // 1000
        minutes = seconds // 60
        seconds %= 60
        
        self.seconds = seconds
        self.minutes = minutes
    
    def __eq__(self, other) -> bool:
        return self.minutes == other.minutes and self.seconds == other.seconds
    
    def __gt__(self, other) -> bool:
        if self.minutes > other.minutes:
            return True
        elif self.minutes == other.minutes:
            return self.seconds > other.seconds
        return False
    
    def __ge__(self, other) -> bool:
        return self > other or self == other
    
    def __lt__(self, other) -> bool:
        return not self >= other
    
    def __le__(self, other) -> bool:
        return not self > other
    
    def __add__(self, other):
        new_time_label = TimeLabel()
        new_time_label.curr_time = self.curr_time
        
        if isinstance(other, int):
            new_time_label.seconds += other
            
        if isinstance(other, TimeLabel):
            new_time_label.miliseconds += other.miliseconds
        
        return new_time_label

        
        
    