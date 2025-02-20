import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkcalendar
import threading
import time
import datetime
import os
from tkinter import messagebox
import json
import pygame
import uuid

class MainWindow:
    def __init__(self, master):
        self.master = master
        master.title("定时播放器")

        # 初始化pygame混音器
        pygame.mixer.init()

        # 初始化任务列表
        self.tasks = []

        # 音频时长缓存
        self.audio_durations = {}
        
        # 跟踪已播放的任务
        self.played_tasks = {}
        
        # 加载任务数据（如果存在）
        self.load_tasks()

        # 时间和日期显示
        self.time_date_frame = tk.Frame(master)
        self.time_date_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.current_time_label = tk.Label(self.time_date_frame, text="当前时间", font=("Helvetica", 12))
        self.current_time_label.pack()

        self.time_label = tk.Label(self.time_date_frame, text="当前时间", font=("Helvetica", 24))
        self.time_label.pack(pady=5)
        self.date_label = tk.Label(self.time_date_frame, text="当前时间", font=("Helvetica", 16))
        self.date_label.pack()

        self.update_time()

        # 按钮
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=5)

        self.add_button = tk.Button(self.button_frame, text="添加任务", command=self.add_task)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(self.button_frame, text="删除任务", command=self.delete_task)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.import_button = tk.Button(self.button_frame, text="导入", command=self.import_tasks)
        self.import_button.pack(side=tk.LEFT, padx=5)

        self.export_button = tk.Button(self.button_frame, text="导出", command=self.export_tasks)
        self.export_button.pack(side=tk.LEFT, padx=5)

        self.play_button = tk.Button(self.button_frame, text="播放", command=self.play_selected)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(self.button_frame, text="暂停", command=self.pause_playing, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(self.button_frame, text="停止", command=self.stop_playing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 初始状态，没有文件播放
        self.is_playing = False
        self.current_playing = None

        # 表格 + 滚动条
        self.tree_frame = tk.Frame(master)
        self.tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.tree_scroll_y = tk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_scroll_x = tk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 表格样式
        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 10))
        style.configure("Treeview.Heading", anchor="w", font=('Arial', 10)) # 表头左对齐
        style.configure("TButton", font=('Arial', 10))
        style.configure("TLabel", font=('Arial', 10))

        self.tree = ttk.Treeview(self.tree_frame, columns=("id", "task", "date", "time", "end_time", "file"), show="headings", yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set, style="Treeview")
        self.tree.heading("id", text="序号")
        self.tree.heading("task", text="事项")
        self.tree.heading("date", text="日期")
        self.tree.heading("time", text="开始时间")
        self.tree.heading("end_time", text="结束时间")
        self.tree.heading("file", text="文件路径")
        self.tree.column("id", width=30, minwidth=30, anchor="w")
        self.tree.column("task", width=150, minwidth=150, anchor="w")
        self.tree.column("date", width=80, minwidth=80, anchor="w")
        self.tree.column("time", width=60, minwidth=60, anchor="w")
        self.tree.column("end_time", width=60, minwidth=60, anchor="w")
        self.tree.column("file", width=200, minwidth=200, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # 双击事件
        self.tree.bind("<Double-1>", self.open_task_window)

        # 任务数据
        self.tasks = []
        self.load_tasks()

        # 上升下降按钮
        self.move_button_frame = tk.Frame(master)
        self.move_button_frame.pack(pady=5)

        self.move_up_button = tk.Button(self.move_button_frame, text="上升", command=self.move_up)
        self.move_up_button.pack(side=tk.LEFT, padx=5)

        self.move_down_button = tk.Button(self.move_button_frame, text="下降", command=self.move_down)
        self.move_down_button.pack(side=tk.LEFT, padx=5)

        # 窗口大小调整
        master.bind("<Configure>", self.on_resize)

        # 表格样式
        self.tree.tag_configure('even', background='#E6F2FF')  # 浅蓝色
        self.tree.tag_configure('odd', background='#FFFFE0')  # 浅黄色

    def pause_playing(self):
        """暂停播放"""
        if self.is_playing:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.is_playing = False
                self.pause_button.config(text="继续")
        elif not self.is_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.pause_button.config(text="暂停")

    def stop_playing(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.pause_button.config(state=tk.DISABLED, text="暂停")
        self.stop_button.config(state=tk.DISABLED)

    def update_time(self):
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%Y-%m-%d"))
        self.master.after(1000, self.update_time)

    def add_task(self):
        TaskWindow(self)

    def open_task_window(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            task_index = int(selected_item[0][1:]) - 1
            TaskWindow(self, task_index=task_index)

    def delete_task(self):
        selected_item = self.tree.selection()
        if messagebox.askokcancel("删除任务", "确定要删除选中的任务吗？"):
            task_index = int(selected_item[0][1:]) - 1
            del self.tasks[task_index]
            self.save_tasks()
            self.update_task_list()

    def import_tasks(self):
        filename = filedialog.askopenfilename(initialdir=".", title="选择播放列表文件", filetypes=(("JSON Files", "*.json"), ("all files", "*.*")))
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    loaded_tasks = json.load(f)
                    # 确保导入的时间精确到秒
                    for task in loaded_tasks:
                        if len(task['time'].split(':')) == 2:
                            task['time'] += ':00'
                        elif len(task['time'].split(':')) == 3:
                            pass
                        else:
                            task['time'] = '00:00:00'
                    self.tasks = loaded_tasks
                self.save_tasks()
                self.update_task_list()
            except Exception as e:
                messagebox.showerror("错误", f"导入文件失败: {e}")

    def export_tasks(self):
        filename = filedialog.asksaveasfilename(initialdir=".", title="保存播放列表文件", filetypes=(("JSON Files", "*.json"), ("all files", "*.*"),("JSON Files", "*.json")))
        if not filename.endswith(".json"):
            filename += ".json"
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.tasks, f, indent=4, ensure_ascii=False)
            except Exception as e:
                messagebox.showerror("错误", f"导出文件失败: {str(e)}")

    def load_tasks(self):
        """加载任务数据"""
        try:
            if os.path.exists("tasks.json"):
                with open("tasks.json", "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            else:
                # 如果文件不存在，创建空的任务列表文件
                self.save_tasks()
            # 确保每个任务都有一个 UUID
            for task in self.tasks:
                if 'uuid' not in task:
                    task['uuid'] = str(uuid.uuid4())
        except Exception as e:
            messagebox.showerror("错误", f"读取任务数据失败: {str(e)}")
            self.tasks = []

    def save_tasks(self):
        """保存任务数据"""
        try:
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存任务失败: {str(e)}")

    def update_task_list(self):
        # 删除所有现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取当前时间信息
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_weekday = now.strftime("%A")

        # 重新插入所有任务
        for i, task in enumerate(self.tasks):
            item_id = f"I{i+1}"  # 使用简单的序号作为item_id而不是UUID
            display_id = str(i + 1)
            file_path = task['file']
            
            # 尝试从缓存中获取音频时长
            duration = self.audio_durations.get(file_path)
            if duration is None:
                try:
                    sound = pygame.mixer.Sound(file_path)
                    duration = sound.get_length()  # 获取音频时长，单位为秒
                    self.audio_durations[file_path] = duration  # 缓存音频时长
                except Exception as e:
                    duration = 0
                    print(f"获取音频时长失败: {str(e)}")

            # 计算结束时间
            start_time = datetime.datetime.strptime(task['time'], "%H:%M:%S")
            end_time = start_time + datetime.timedelta(seconds=duration)
            end_time_str = end_time.strftime("%H:%M:%S")

            # 检查任务状态
            if "," in task['date']:  # 周循环任务
                weekdays = task['date'].split(",")
                if current_weekday in weekdays and task['time'] < current_time:
                    display_id += " (已播放)"
            elif task['date'] <= now.strftime("%Y-%m-%d") and task['time'] < current_time:
                display_id += " (已播放)"

            # 插入任务到树形列表
            self.tree.insert("", "end", iid=item_id, values=(display_id, task['task'], task['date'], task['time'], end_time_str, task['file']))

    def play_selected(self):
        selected_item = self.tree.selection()
        if selected_item:
            selected_id = selected_item[0]  # 获取选中项的UUID
            # 查找对应的任务
            for task in self.tasks:
                if task['uuid'] == selected_id:
                    file_path = task['file']
                    try:
                        # 停止当前正在播放的音频
                        if self.current_playing != file_path:
                            pygame.mixer.music.stop()
                        # 加载并播放新的音频文件
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.play()
                        print(f"正在播放: {file_path}")
                        self.is_playing = True
                        self.pause_button.config(state=tk.NORMAL)
                        self.stop_button.config(state=tk.NORMAL)
                        self.current_playing = file_path
                    except Exception as e:
                        messagebox.showerror("错误", f"播放失败: {str(e)}")
                    break

    def add_new_task(self, task):
        self.tasks.append(task)
        self.save_tasks()
        self.update_task_list()

    def update_existing_task(self, task_index, task):
        self.tasks[task_index] = task
        self.save_tasks()
        self.update_task_list()

    def move_up(self):
        selected_item = self.tree.selection()
        if selected_item:
            task_index = int(selected_item[0][1:]) - 1
            if task_index > 0:
                self.tasks[task_index], self.tasks[task_index - 1] = self.tasks[task_index - 1], self.tasks[task_index]
                self.save_tasks()
                self.update_task_list()
                self.tree.selection_set(f"I{task_index}")

    def move_down(self):
        selected_item = self.tree.selection()
        if selected_item:
            task_index = int(selected_item[0][1:]) - 1
            if task_index < len(self.tasks) - 1:
                self.tasks[task_index], self.tasks[task_index + 1] = self.tasks[task_index + 1], self.tasks[task_index]
                self.save_tasks()
                self.update_task_list()
                self.tree.selection_set(f"I{task_index+1}")

    def on_resize(self, event):
        width = event.width
        #height = event.height
        self.tree.column("id", width=int(width*0.05), minwidth=30)
        self.tree.column("task", width=int(width*0.2), minwidth=150)
        self.tree.column("date", width=int(width*0.1), minwidth=80)
        self.tree.column("time", width=int(width*0.1), minwidth=60)
        self.tree.column("end_time", width=int(width*0.1), minwidth=60)
        self.tree.column("file", width=int(width*0.3), minwidth=200)

class TaskWindow:
    def __init__(self, main_window, task_index=None):
        self.main_window = main_window
        self.task_index = task_index
        self.top = tk.Toplevel(main_window.master)
        self.top.title("添加/编辑任务")

        # 选择日期类型
        self.date_type_label = tk.Label(self.top, text="选择日期类型:")
        self.date_type_label.grid(row=0, column=0, padx=5, pady=5)
        self.date_type_var = tk.StringVar(value="weekday")
        self.specific_date_radio = tk.Radiobutton(self.top, text="指定日期", variable=self.date_type_var, value="specific_date", command=self.update_date_options)
        self.specific_date_radio.grid(row=0, column=1, padx=5, pady=5)
        self.weekday_radio = tk.Radiobutton(self.top, text="周循环", variable=self.date_type_var, value="weekday", command=self.update_date_options)
        self.weekday_radio.grid(row=0, column=2, padx=5, pady=5)

        # 特定日期选择
        self.date_label = tk.Label(self.top, text="选择日期:")
        self.date_label.grid(row=1, column=0, padx=5, pady=5)
        self.cal = tkcalendar.Calendar(self.top, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

        # 星期几选择
        self.weekday_label = tk.Label(self.top, text="选择星期几:")
        self.weekday_label.grid(row=2, column=0, padx=5, pady=5)
        self.monday_var = tk.BooleanVar(value=False)
        self.monday_check = tk.Checkbutton(self.top, text="星期一", variable=self.monday_var)
        self.monday_check.grid(row=2, column=1, padx=5, pady=5)
        self.tuesday_var = tk.BooleanVar(value=False)
        self.tuesday_check = tk.Checkbutton(self.top, text="星期二", variable=self.tuesday_var)
        self.tuesday_check.grid(row=2, column=2, padx=5, pady=5)
        self.wednesday_var = tk.BooleanVar(value=False)
        self.wednesday_check = tk.Checkbutton(self.top, text="星期三", variable=self.wednesday_var)
        self.wednesday_check.grid(row=3, column=1, padx=5, pady=5)
        self.thursday_var = tk.BooleanVar(value=False)
        self.thursday_check = tk.Checkbutton(self.top, text="星期四", variable=self.thursday_var)
        self.thursday_check.grid(row=3, column=2, padx=5, pady=5)
        self.friday_var = tk.BooleanVar(value=False)
        self.friday_check = tk.Checkbutton(self.top, text="星期五", variable=self.friday_var)
        self.friday_check.grid(row=4, column=1, padx=5, pady=5)
        self.saturday_var = tk.BooleanVar(value=False)
        self.saturday_check = tk.Checkbutton(self.top, text="星期六", variable=self.saturday_var)
        self.saturday_check.grid(row=4, column=2, padx=5, pady=5)
        self.sunday_var = tk.BooleanVar(value=False)
        self.sunday_check = tk.Checkbutton(self.top, text="星期日", variable=self.sunday_var)
        self.sunday_check.grid(row=5, column=1, padx=5, pady=5)

        # 时间选择
        self.time_label = tk.Label(self.top, text="选择时间:")
        self.time_label.grid(row=6, column=0, padx=5, pady=5)

        self.time_frame = tk.Frame(self.top)
        self.time_frame.grid(row=6, column=1, columnspan=6, padx=0, pady=0, sticky="w")

        # 获取上一条任务的结束时间
        last_time = "00:00:00"
        if main_window.tasks and task_index is None:  # 添加新任务时
            try:
                last_task = main_window.tasks[-1]
                last_time = last_task.get('end_time', "00:00:00")  # 使用get方法，提供默认值00:00:00
            except:
                pass

        # 设置时间选择器的初始值
        if len(main_window.tasks) > 0 and task_index is None:
            self.hour_var = tk.StringVar(value=last_time[:2])      # 小时
            self.minute_var = tk.StringVar(value=last_time[3:5])   # 分钟
            self.second_var = tk.StringVar(value=last_time[6:8])   # 秒钟
        else:
            self.hour_var = tk.StringVar(value="00")
            self.minute_var = tk.StringVar(value="00")
            self.second_var = tk.StringVar(value="00")

        self.hour_spinbox = tk.Spinbox(self.time_frame, from_=0, to=23, width=3, textvariable=self.hour_var, format="%02.0f")
        self.hour_spinbox.pack(side=tk.LEFT, padx=1, pady=0)
        self.hour_label = tk.Label(self.time_frame, text="时")
        self.hour_label.pack(side=tk.LEFT, padx=1, pady=0)
        self.minute_spinbox = tk.Spinbox(self.time_frame, from_=0, to=59, width=3, textvariable=self.minute_var, format="%02.0f")
        self.minute_spinbox.pack(side=tk.LEFT, padx=1, pady=0)
        self.minute_label = tk.Label(self.time_frame, text="分")
        self.minute_label.pack(side=tk.LEFT, padx=1, pady=0)
        self.second_spinbox = tk.Spinbox(self.time_frame, from_=0, to=59, width=3, textvariable=self.second_var, format="%02.0f")
        self.second_spinbox.pack(side=tk.LEFT, padx=1, pady=0)
        self.second_label = tk.Label(self.time_frame, text="秒")
        self.second_label.pack(side=tk.LEFT, padx=1, pady=0)

        # 任务
        self.task_label = tk.Label(self.top, text="事项:")
        self.task_label.grid(row=7, column=0, padx=5, pady=5)
        self.task_entry = tk.Entry(self.top)
        self.task_entry.grid(row=7, column=1, padx=5, pady=5)

        # 文件选择
        self.file_label = tk.Label(self.top, text="选择文件:")
        self.file_label.grid(row=8, column=0, padx=5, pady=5)
        self.file_entry = tk.Entry(self.top)
        self.file_entry.grid(row=8, column=1, padx=5, pady=5)
        self.file_button = tk.Button(self.top, text="浏览", command=self.browse_file)
        self.file_button.grid(row=8, column=2, padx=5, pady=5)

        # 保存和取消按钮
        self.save_button = tk.Button(self.top, text="保存", command=self.save_task)
        self.save_button.grid(row=9, column=0, padx=5, pady=5)
        self.cancel_button = tk.Button(self.top, text="取消", command=self.top.destroy)
        self.cancel_button.grid(row=9, column=1, padx=5, pady=5)

        # 删除按钮
        if task_index is not None:
            self.delete_button = tk.Button(self.top, text="删除", command=self.delete_task)
            self.delete_button.grid(row=9, column=2, padx=5, pady=5)
            task = main_window.tasks[task_index]
            if task['date'] == "specific_date":
                self.date_type_var.set("specific_date")
                self.cal.selection_set(task['date'])
                self.hour_var.set(task['time'][:2])
                self.minute_var.set(task['time'][3:5])
                self.second_var.set(task['time'][6:8])
            else:
                self.date_type_var.set("weekday")
                weekdays = task['date'].split(",")
                self.monday_var.set("Monday" in weekdays)
                self.tuesday_var.set("Tuesday" in weekdays)
                self.wednesday_var.set("Wednesday" in weekdays)
                self.thursday_var.set("Thursday" in weekdays)
                self.friday_var.set("Friday" in weekdays)
                self.saturday_var.set("Saturday" in weekdays)
                self.sunday_var.set("Sunday" in weekdays)
                self.hour_var.set(task['time'][:2])
                self.minute_var.set(task['time'][3:5])
                self.second_var.set(task['time'][6:8])
            self.file_entry.insert(0, task['file'])
            self.task_entry.insert(0, task['task'])

        self.update_date_options()

    def update_date_options(self):
        date_type = self.date_type_var.get()
        if date_type == "specific_date":
            self.date_label.grid(row=1, column=0, padx=5, pady=5)
            self.cal.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
            self.weekday_label.grid_remove()
            self.monday_check.grid_remove()
            self.tuesday_check.grid_remove()
            self.wednesday_check.grid_remove()
            self.thursday_check.grid_remove()
            self.friday_check.grid_remove()
            self.saturday_check.grid_remove()
            self.sunday_check.grid_remove()
            if hasattr(self, 'weekday_button'):
                self.weekday_button.destroy()
                del self.weekday_button
        else:
            self.date_label.grid_remove()
            self.cal.grid_remove()
            self.weekday_label.grid(row=2, column=0, padx=5, pady=5)
            self.monday_check.grid(row=2, column=1, padx=5, pady=5)
            self.tuesday_check.grid(row=2, column=2, padx=5, pady=5)
            self.wednesday_check.grid(row=3, column=1, padx=5, pady=5)
            self.thursday_check.grid(row=3, column=2, padx=5, pady=5)
            self.friday_check.grid(row=4, column=1, padx=5, pady=5)
            self.saturday_check.grid(row=4, column=2, padx=5, pady=5)
            self.sunday_check.grid(row=5, column=1, padx=5, pady=5)
            self.weekday_button = tk.Button(self.top, text="工作日", command=self.select_weekdays)
            self.weekday_button.grid(row=5, column=2, padx=5, pady=5)

    def select_weekdays(self):
        self.monday_var.set(True)
        self.tuesday_var.set(True)
        self.wednesday_var.set(True)
        self.thursday_var.set(True)
        self.friday_var.set(True)

    def browse_file(self):
        filename = filedialog.askopenfilename(initialdir=".", title="选择音频文件", filetypes=(("Audio Files", "*.mp3;*.wav"), ("all files", "*.*")))
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, filename)

    def save_task(self):
        date_type = self.date_type_var.get()
        if date_type == "specific_date":
            date = self.cal.get_date()
        else:
            weekdays = []
            if self.monday_var.get():
                weekdays.append("Monday")
            if self.tuesday_var.get():
                weekdays.append("Tuesday")
            if self.wednesday_var.get():
                weekdays.append("Wednesday")
            if self.thursday_var.get():
                weekdays.append("Thursday")
            if self.friday_var.get():
                weekdays.append("Friday")
            if self.saturday_var.get():
                weekdays.append("Saturday")
            if self.sunday_var.get():
                weekdays.append("Sunday")
            date = ",".join(weekdays)
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        second = self.second_var.get()
        try:
            datetime.datetime.strptime(f"{hour}:{minute}:{second}", "%H:%M:%S")
        except ValueError:
            messagebox.showerror("错误", "时间格式不正确，请输入HH:MM:SS格式的时间")
            return
        time = f"{hour}:{minute}:{second}"
        file = self.file_entry.get()
        if not file:
            messagebox.showerror("错误", "请选择文件")
            return
        task_content = self.task_entry.get()
        # 计算结束时间
        try:
            sound = pygame.mixer.Sound(file)
            duration = sound.get_length()  # 获取音频时长，单位为秒
            start_time = datetime.datetime.strptime(time, "%H:%M:%S")
            end_time = start_time + datetime.timedelta(seconds=duration)
            end_time_str = end_time.strftime("%H:%M:%S")
        except Exception as e:
            end_time_str = "00:00:00"
            print(f"获取音频时长失败: {str(e)}")
        task = {"date": date, "time": time, "file": file, "task":task_content, "end_time": end_time_str, "uuid": str(uuid.uuid4())}
        if self.task_index is None:
            self.main_window.add_new_task(task)
        else:
            self.main_window.update_existing_task(self.task_index, task)
        self.top.destroy()

    def delete_task(self):
        self.main_window.delete_task(self.task_index)
        self.top.destroy()

def main():
    root = tk.Tk()
    main_window = MainWindow(root)

    def check_tasks():
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")
        current_weekday = now.strftime("%A")
        
        # 每天零点重置已播放任务记录
        if current_time == "00:00:00":
            main_window.played_tasks.clear()

        for task in main_window.tasks:
            task_time = task['time']
            
            # 检查是否是周期性任务
            is_weekday_task = "," in task['date']
            
            # 对于周期性任务，检查当前是否是指定的工作日
            if is_weekday_task:
                weekdays = task['date'].split(",")
                should_play = current_weekday in weekdays
                task_key = f"{current_date}_{task_time}_{task['file']}"
            else:
                # 对于特定日期任务
                should_play = task['date'] == current_date
                task_key = f"{task['date']}_{task_time}_{task['file']}"

            # 检查时间是否匹配（精确到秒）和任务是否已播放
            if should_play and current_time == task_time and task_key not in main_window.played_tasks:
                try:
                    file_path = task['file']
                    if not os.path.exists(file_path):
                        print(f"文件不存在: {file_path}")
                        continue
                        
                    # 停止当前播放
                    if main_window.current_playing != file_path:
                        pygame.mixer.music.stop()
                        
                    # 加载并播放新文件
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    print(f"定时播放: {file_path} at {current_time}")
                    main_window.current_playing = file_path
                    main_window.is_playing = True
                    main_window.pause_button.config(state=tk.NORMAL)
                    main_window.stop_button.config(state=tk.NORMAL)
                    
                    # 标记任务已播放
                    main_window.played_tasks[task_key] = True
                except Exception as e:
                    print(f"播放失败: {str(e)}")

        # 每1秒检查一次
        root.after(1000, check_tasks)

    # 初始加载时排序
    main_window.tasks.sort(key=lambda x: x['time'])
    main_window.update_task_list()
    
    # 启动任务检查
    check_tasks()
    
    root.mainloop()

if __name__ == "__main__":
    main()
