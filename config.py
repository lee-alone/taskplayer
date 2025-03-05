from dataclasses import dataclass
import os

@dataclass
class UIConfig:
    WINDOW_SIZE = "1024x768"
    MIN_WINDOW_SIZE = (800, 600)
    TITLE_FONT = ("Segoe UI", 12, "bold")
    NORMAL_FONT = ("Segoe UI", 10)
    
    # 颜色配置
    PRIMARY_COLOR = "#26A69A"
    SECONDARY_COLOR = "#B2DFDB"
    BACKGROUND_COLOR = "#ECEFF1"

@dataclass 
class PathConfig:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
    TASK_FILE_PATH = os.path.join(BASE_DIR, "task.json")

@dataclass
class TaskConfig:
    WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]
    DEFAULT_VOLUME = 100
    DEFAULT_STATUS = "waiting"
