import tkinter as tk
from tkinter import ttk
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.task_manager import TaskManager
from core.audio_player import AudioPlayer
from gui.task_dialog import TaskDialog  # 修改这里：task_window -> task_dialog
from utils.time_utils import calculate_end_time
import datetime

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.task_manager = TaskManager()
        self.audio_player = AudioPlayer()
        self.setup_window()
        self.create_ui()
        self.start_monitoring()

    def add_task(self):
        dialog = TaskDialog(self.master)  # 这里也要相应修改
        result = dialog.get_result()
        if result:
            self.task_manager.add_task(result)
            self.update_task_list()
            
    # ...其他方法保持不变...
