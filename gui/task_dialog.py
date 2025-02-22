import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import uuid
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.time_utils import format_time

class TaskDialog:
    def __init__(self, parent, task=None):
        self.parent = parent
        self.task = task
        self.top = tk.Toplevel(parent)
        self.top.title("添加/编辑任务")
        self.result = None
        self._init_variables()
        self._create_ui()
        if task:
            self._load_task(task)
            
    def _init_variables(self):
        self.date_type = tk.StringVar(value="weekday")
        self.hour = tk.StringVar(value="00")
        self.minute = tk.StringVar(value="00")
        self.second = tk.StringVar(value="00")
        self.weekdays = {
            'Monday': tk.BooleanVar(),
            'Tuesday': tk.BooleanVar(),
            'Wednesday': tk.BooleanVar(),
            'Thursday': tk.BooleanVar(),
            'Friday': tk.BooleanVar(),
            'Saturday': tk.BooleanVar(),
            'Sunday': tk.BooleanVar()
        }
        
    def _create_ui(self):
        self._create_date_section()
        self._create_time_section()
        self._create_file_section()
        self._create_buttons()
        
    def _create_date_section(self):
        date_frame = tk.LabelFrame(self.top, text="日期设置")
        date_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Radiobutton(date_frame, text="按星期", 
                      variable=self.date_type,
                      value="weekday").pack(anchor="w")
                      
        weekday_frame = tk.Frame(date_frame)
        weekday_frame.pack(fill="x", padx=20)
        
        for day in self.weekdays:
            tk.Checkbutton(weekday_frame, text=day,
                          variable=self.weekdays[day]).pack(side=tk.LEFT)
                          
        tk.Radiobutton(date_frame, text="指定日期",
                      variable=self.date_type,
                      value="specific").pack(anchor="w")
                      
        self.date_entry = tk.Entry(date_frame)
        self.date_entry.pack(padx=20, fill="x")
        
    def _create_time_section(self):
        time_frame = tk.LabelFrame(self.top, text="时间设置")
        time_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Entry(time_frame, textvariable=self.hour, width=2).pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        tk.Entry(time_frame, textvariable=self.minute, width=2).pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        tk.Entry(time_frame, textvariable=self.second, width=2).pack(side=tk.LEFT)
        
    def _create_file_section(self):
        file_frame = tk.LabelFrame(self.top, text="音频文件")
        file_frame.pack(fill="x", padx=5, pady=5)
        
        self.file_entry = tk.Entry(file_frame)
        self.file_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        
        tk.Button(file_frame, text="选择文件",
                 command=self._choose_file).pack(side=tk.LEFT)
                 
    def _create_buttons(self):
        btn_frame = tk.Frame(self.top)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="确定",
                 command=self._on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消",
                 command=self.top.destroy).pack(side=tk.LEFT, padx=5)

    def _choose_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("音频文件", "*.mp3;*.wav")]
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)

    def _on_ok(self):
        try:
            task_data = self._collect_data()
            self._validate_data(task_data)
            self.result = task_data
            self.top.destroy()
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def _collect_data(self):
        # ...实现数据收集逻辑...
        pass

    def _validate_data(self, data):
        # ...实现数据验证逻辑...
        pass

    def _load_task(self, task):
        # ...实现任务加载逻辑...
        pass

    def get_result(self):
        self.top.wait_window()
        return self.result
