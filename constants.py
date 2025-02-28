import os

# 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
TASK_FILE_PATH = os.path.join(BASE_DIR, "task.json")

# 窗口设置
DEFAULT_WINDOW_SIZE = "1024x768"
MIN_WINDOW_SIZE = (800, 600)

# 字体设置
TITLE_FONT = ("Segoe UI", 14, "bold")  # Or "Arial" if Segoe UI unavailable
NORMAL_FONT = ("Segoe UI", 11)

# 颜色设置
PRIMARY_COLOR = "#26A69A"    # Teal
SECONDARY_COLOR = "#B2DFDB"  # Light Teal
BACKGROUND_COLOR = "#ECEFF1" # Light Gray

# 其他常量
WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]