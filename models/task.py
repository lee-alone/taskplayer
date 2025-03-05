from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    """任务数据模型"""
    id: str
    name: str  
    start_time: str
    end_time: str
    volume: int
    schedule: str
    audio_path: str
    status: str = "waiting"
    
    @property
    def is_playing(self) -> bool:
        return self.status == "正在播放"
        
    @property  
    def is_paused(self) -> bool:
        return self.status == "已暂停"
        
    @property
    def is_paused_today(self) -> bool:
        return self.status == "Pause today"
        
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=str(data["id"]),
            name=data["name"],
            start_time=data["startTime"],
            end_time=data["endTime"], 
            volume=int(data["volume"]),
            schedule=data["schedule"],
            audio_path=data["audioPath"],
            status=data.get("status", "waiting")
        )
        
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "volume": self.volume,
            "schedule": self.schedule,
            "audioPath": self.audio_path,
            "status": self.status
        }
