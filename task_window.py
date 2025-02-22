import tkinter as tk
from tkinter import filedialog
import datetime
import pygame
import uuid
from utils import format_time, calculate_end_time

class TaskWindow:
    def __init__(self, main_window, task_index=None):
        self.main_window = main_window
        self.task_index = task_index
        self.setup_window()
        self.create_ui()
        self.load_task_data()

    def setup_window(self):
        self.top = tk.Toplevel(self.main_window.master)
        self.top.title("添加/编辑任务")
        self.setup_variables()

    def setup_variables(self):
        self.date_type_var = tk.StringVar(value="weekday")
        self.setup_time_variables()
        self.setup_weekday_variables()

    def create_ui(self):
        self.create_date_options()
        self.create_time_selector()
        self.create_task_inputs()
        self.create_buttons()

    def load_task_data(self):
        if self.task_index is not None:
            task = self.main_window.tasks[self.task_index]
            self.load_existing_task(task)

    def save_task(self):
        try:
            task_data = self.collect_task_data()
            self.validate_task_data(task_data)
            self.save_task_data(task_data)
            self.top.destroy()
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def collect_task_data(self):
        # ...existing code...

    def validate_task_data(self, task_data):
        # ...existing code...

    # ... other existing methods ...
