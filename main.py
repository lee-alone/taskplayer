import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import pygame
from task_window import TaskWindow
from request import load_tasks, save_tasks, import_tasks, export_tasks
from utils import format_time, calculate_end_time

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.setup_window()
        self.setup_pygame()
        self.init_variables()
        self.create_ui()
        self.load_data()
        self.start_monitoring()

    def setup_window(self):
        self.master.title("定时播放器")
        self.master.bind("<Configure>", self.on_resize)
        
    def setup_pygame(self):
        pygame.mixer.init()
        
    def init_variables(self):
        self.tasks = []
        self.audio_durations = {}
        self.played_tasks = {}
        self.is_playing = False
        self.current_playing = None

    def create_ui(self):
        self.create_time_display()
        self.create_buttons()
        self.create_task_list()
        self.create_movement_buttons()

    def create_time_display(self):
        self.time_date_frame = tk.Frame(self.master)
        self.time_date_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.current_time_label = tk.Label(self.time_date_frame, text="当前时间", font=("Helvetica", 12))
        self.current_time_label.pack()

        self.time_label = tk.Label(self.time_date_frame, text="当前时间", font=("Helvetica", 24))
        self.time_label.pack(pady=5)
        self.date_label = tk.Label(self.time_date_frame, text="当前时间", font=("Helvetica", 16))
        self.date_label.pack()

        self.update_time()

    def create_buttons(self):
        self.button_frame = tk.Frame(self.master)
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

        self.sort_button = tk.Button(self.button_frame, text="排序", command=self.sort_tasks)
        self.sort_button.pack(side=tk.LEFT, padx=5)

    def create_task_list(self):
        self.tree_frame = tk.Frame(self.master)
        self.tree_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.tree_scroll_y = tk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_scroll_x = tk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 10))
        style.configure("Treeview.Heading", anchor="w", font=('Arial', 10))
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

        self.tree.bind("<Double-1>", self.open_task_window)

        self.tree.tag_configure('even', background='#E6F2FF')
        self.tree.tag_configure('odd', background='#FFFFE0')

    def create_movement_buttons(self):
        self.move_button_frame = tk.Frame(self.master)
        self.move_button_frame.pack(pady=5)

        self.move_up_button = tk.Button(self.move_button_frame, text="上升", command=self.move_up)
        self.move_up_button.pack(side=tk.LEFT, padx=5)

        self.move_down_button = tk.Button(self.move_button_frame, text="下降", command=self.move_down)
        self.move_down_button.pack(side=tk.LEFT, padx=5)

    def load_data(self):
        self.tasks = load_tasks()
        self.tasks.sort(key=lambda x: x['time'])
        self.update_task_list()

    def start_monitoring(self):
        def check_tasks():
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M:%S")
            
            if current_time == "00:00:00":
                self.played_tasks.clear()

            self.check_and_play_tasks(now)
            self.master.after(1000, check_tasks)

        check_tasks()

    def check_and_play_tasks(self, now):
        for task in self.tasks:
            if self.should_play_task(task, now):
                self.play_task(task)

    def should_play_task(self, task, now):
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")
        current_weekday = now.strftime("%A")
        
        is_weekday_task = "," in task['date']
        
        if is_weekday_task:
            weekdays = task['date'].split(",")
            should_play = current_weekday in weekdays
            task_key = f"{current_date}_{task['time']}_{task['file']}"
        else:
            should_play = task['date'] == current_date
            task_key = f"{task['date']}_{task['time']}_{task['file']}"

        if should_play and abs(datetime.datetime.strptime(current_time, "%H:%M:%S") - datetime.datetime.strptime(task['time'], "%H:%M:%S")).total_seconds() <= 1 and task_key not in self.played_tasks:
            return True
        return False

    def play_task(self, task):
        try:
            file_path = task['file']
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            self.stop_current_playback()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.update_playback_status(file_path)
            
        except Exception as e:
            messagebox.showerror("播放错误", str(e))

    def stop_current_playback(self):
        if self.current_playing:
            pygame.mixer.music.stop()

    def update_playback_status(self, file_path):
        self.is_playing = True
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.current_playing = file_path

    def pause_playing(self):
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
            save_tasks(self.tasks)
            self.update_task_list()

    def import_tasks(self):
        self.tasks = import_tasks()
        save_tasks(self.tasks)
        self.update_task_list()

    def export_tasks(self):
        export_tasks(self.tasks)

    def update_task_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_weekday = now.strftime("%A")

        for i, task in enumerate(self.tasks):
            item_id = f"I{i+1}"
            display_id = str(i + 1)
            file_path = task['file']
            
            duration = self.audio_durations.get(file_path)
            if duration is None:
                try:
                    sound = pygame.mixer.Sound(file_path)
                    duration = sound.get_length()
                    self.audio_durations[file_path] = duration
                except Exception as e:
                    duration = 0
                    print(f"获取音频时长失败: {str(e)}")

            start_time = datetime.datetime.strptime(task['time'], "%H:%M:%S")
            end_time = start_time + datetime.timedelta(seconds=duration)
            end_time_str = end_time.strftime("%H:%M:%S")

            if "," in task['date']:
                weekdays = task['date'].split(",")
                if current_weekday in weekdays and task['time'] < current_time:
                    display_id += " (已播放)"
            elif task['date'] <= now.strftime("%Y-%m-%d") and task['time'] < current_time:
                display_id += " (已播放)"

            self.tree.insert("", "end", iid=item_id, values=(display_id, task['task'], task['date'], task['time'], end_time_str, task['file']))

    def play_selected(self):
        selected_item = self.tree.selection()
        if selected_item:
            selected_id = selected_item[0]
            task_index = int(selected_id[1:]) - 1
            if 0 <= task_index < len(self.tasks):
                task = self.tasks[task_index]
                file_path = task['file']
                try:
                    if self.current_playing != file_path:
                        pygame.mixer.music.stop()
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.pause_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.NORMAL)
                    self.current_playing = file_path
                except Exception as e:
                    messagebox.showerror("错误", f"播放失败: {str(e)}")

    def add_new_task(self, task):
        self.tasks.append(task)
        save_tasks(self.tasks)
        self.update_task_list()

    def update_existing_task(self, task_index, task):
        self.tasks[task_index] = task
        save_tasks(self.tasks)
        self.update_task_list()

    def move_up(self):
        selected_item = self.tree.selection()
        if selected_item:
            task_index = int(selected_item[0][1:]) - 1
            if task_index > 0:
                self.tasks[task_index], self.tasks[task_index - 1] = self.tasks[task_index - 1], self.tasks[task_index]
                save_tasks(self.tasks)
                self.update_task_list()
                self.tree.selection_set(f"I{task_index}")

    def move_down(self):
        selected_item = self.tree.selection()
        if selected_item:
            task_index = int(selected_item[0][1:]) - 1
            if task_index < len(self.tasks) - 1:
                self.tasks[task_index], self.tasks[task_index + 1] = self.tasks[task_index + 1], self.tasks[task_index]
                save_tasks(self.tasks)
                self.update_task_list()
                self.tree.selection_set(f"I{task_index+1}")

    def on_resize(self, event):
        width = event.width
        self.tree.column("id", width=int(width*0.05), minwidth=30)
        self.tree.column("task", width=int(width*0.2), minwidth=150)
        self.tree.column("date", width=int(width*0.1), minwidth=80)
        self.tree.column("time", width=int(width*0.1), minwidth=60)
        self.tree.column("end_time", width=int(width*0.1), minwidth=60)
        self.tree.column("file", width=int(width*0.3), minwidth=200)

    def sort_tasks(self):
        try:
            self.tasks.sort(key=lambda x: x['time'])
            self.update_task_list()
        except KeyError:
            messagebox.showerror("错误", "无法按时间排序，请检查任务数据")

def main():
    root = tk.Tk()
    main_window = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
