import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import threading
import time
import datetime
import pygame
import logging
from constants import TASK_FILE_PATH, ICON_PATH, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, TITLE_FONT, NORMAL_FONT, PRIMARY_COLOR, SECONDARY_COLOR, BACKGROUND_COLOR
from add_task_window import AddTaskWindow
from utils import safe_play_audio, update_task_in_json, load_tasks, save_all_tasks

class ToolTip:
    """A simple tooltip class for displaying hover hints."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    
    def show_tip(self, event):
        x, y = self.widget.winfo_pointerxy()
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x+10}+{y+10}")
        label = tk.Label(self.tip, text=self.text, bg="#FFFFE0", fg="black", relief="solid", borderwidth=1, font=NORMAL_FONT)
        label.pack()
    
    def hide_tip(self, event):
        if self.tip:
            self.tip.destroy()
            self.tip = None
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AudioPlayer:
    def __init__(self):
        self.setup_root_window()
        self.init_variables()
        self.setup_styles()
        self.create_main_layout()
        self.setup_components()
        self.load_tasks()
        self.start_periodic_checks()

    def setup_root_window(self):
        self.root = tk.Tk()
        self.root.title("任务播放器")
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.configure(bg=BACKGROUND_COLOR)
        self._set_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        # Add container for shadow effect
        container = tk.Frame(self.root, bg="#B0BEC5", padx=5, pady=5)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_frame = ttk.Frame(container)
        self.main_frame.pack(fill="both", expand=True)
    def init_variables(self):
        pygame.init()
        pygame.mixer.init()
        self.current_playing_sound = None
        self.paused = False
        self.current_playing_duration = 0
        self.current_playing_position = 0
        self.playing_thread = None
        self.stop_thread = False
        self.current_playing_item = None
        self.current_time = None
        self.total_time = None

    def on_window_close(self):
        self.sort_and_save_tasks()
        self.root.destroy()

    def sort_and_save_tasks(self):
        tasks = []
        for item in self.tree.get_children():
            values = list(self.tree.item(item)["values"])
            task_data = {
                "id": values[0],
                "name": values[1],
                "startTime": values[2],
                "endTime": values[3],
                "volume": values[4],
                "schedule": values[5],
                "audioPath": values[6],
                "status": values[7] if len(values) > 7 else "waiting"
            }
            tasks.append(task_data)
        tasks.sort(key=lambda x: x['startTime'])
        if save_all_tasks(tasks):
            self.status_label.config(text="任务已排序并保存")
        else:
            self.status_label.config(text="保存任务失败")

    def _set_icon(self):
        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except tk.TclError as e:
                logging.warning(f"Could not load icon: {e}")

    def setup_styles(self):
        """Configure ttk widget styles for the application."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=BACKGROUND_COLOR, fieldbackground=BACKGROUND_COLOR, foreground="#37474F", font=NORMAL_FONT, rowheight=30)
        style.configure("Treeview.Heading", background=PRIMARY_COLOR, foreground="white", font=TITLE_FONT, relief="flat", padding=(10, 5))
        style.map("Treeview.Heading", background=[('active', SECONDARY_COLOR)])
        style.map("Treeview", background=[('selected', PRIMARY_COLOR)], foreground=[('selected', 'white')], highlightthickness=[('hover', 1)])
        style.configure("Custom.TButton", font=NORMAL_FONT, padding=(12, 6), borderwidth=0, background=PRIMARY_COLOR, foreground="white")
        style.map("Custom.TButton", background=[('active', SECONDARY_COLOR), ('pressed', "#00897B")], foreground=[('active', 'white')])
        style.configure("Horizontal.TProgressbar", background=PRIMARY_COLOR, troughcolor="#f5f5f5", bordercolor="#e0e0e0", lightcolor="#64b5f6", darkcolor=SECONDARY_COLOR)
        style.configure("Custom.TLabel", font=NORMAL_FONT)
        style.configure("Title.TLabel", font=TITLE_FONT)
        style.configure("TSeparator", background="#e0e0e0")
        style.configure("TFrame", background=BACKGROUND_COLOR)
        style.configure("TLabelframe", background=BACKGROUND_COLOR, padding=5)
        style.configure("TLabelframe.Label", font=TITLE_FONT, foreground="#424242")


    def create_main_layout(self):
        """Set up the main layout with fully responsive grid."""
        main_frame = ttk.Frame(self.main_frame)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        self.task_frame = ttk.Frame(main_frame)
        self.task_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Configure weights for even distribution
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=3)  # Treeview gets more space
        main_frame.grid_rowconfigure(1, weight=1)  # Buttons get moderate space
        main_frame.grid_rowconfigure(2, weight=1)  # Status bar gets minimal space
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def setup_components(self):
        self.setup_tree()
        self.setup_playback_controls()
        self.setup_status_bar()
        
    def setup_tree(self):
        """Set up the Treeview widget for responsive resizing."""
        tree_frame = ttk.Frame(self.task_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        self.columns = ("序号", "任务名称", "开始时间", "结束时间", "音量", "播放日期/星期", "文件路径", "状态")
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings", selectmode="browse", style="Treeview")
        column_widths = {"序号": 50, "任务名称": 180, "开始时间": 80, "结束时间": 80, "音量": 60, "播放日期/星期": 120, "文件路径": 250, "状态": 80}
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=column_widths[col], minwidth=column_widths[col], anchor="center" if col not in ["文件路径", "任务名称"] else "w", stretch=True)
        # Configure Treeview tags
        self.tree.tag_configure('playing', foreground='#4CAF50', background='#E8F5E9')
        self.tree.tag_configure('paused', foreground='#FFA000', background='#FFF3E0')
        self.tree.tag_configure('waiting', foreground='#757575')
        self.tree.tag_configure('error', foreground='#F44336', background='#FFEBEE')
        self.tree.tag_configure('selected', background='#E3F2FD')
        self.tree.tag_configure('oddrow', background="#F5F7FA")
        self.tree.tag_configure('evenrow', background=BACKGROUND_COLOR)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))


    def toggle_playback(self, event=None):
        """Toggle playback state of the selected or currently playing task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要播放的任务")
            return
        item = selected[0]
        
        if not self.current_playing_sound or self.current_playing_sound == "":
            self.play_task(item)
        elif item == self.current_playing_item:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.update_task_status(item, "正在播放", 'playing')
                self.play_buttons_ref["播放/暂停"].config(text="⏸ 暂停")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.update_task_status(item, "已暂停", 'paused')
                self.play_buttons_ref["播放/暂停"].config(text="▶ 继续")
        else:
            self.stop_task()
            self.play_task(item)

    def setup_playback_controls(self):
        """Set up playback control buttons with even distribution."""
        controls_main_frame = tk.Frame(self.control_frame, bg=BACKGROUND_COLOR)
        controls_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.control_frame.grid_columnconfigure(0, weight=1)
        
        # Use grid for even spacing
        left_buttons_frame = tk.Frame(controls_main_frame, bg=BACKGROUND_COLOR)
        left_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 20))
        left_buttons = [
            ("新增任务", "🆕", self.add_task, "添加新任务"),
            ("删除任务", "❌", self.delete_task, "删除选中任务"),
            ("复制任务", "📋", self.copy_task, "复制选中任务"),
            ("导入任务", "📥", self.import_tasks, "从文件导入任务"),
            ("导出任务", "📤", self.export_tasks, "导出任务到文件"),
        ]
        for i, (text, icon, command, tooltip) in enumerate(left_buttons):
            btn = ttk.Button(left_buttons_frame, text=f"{icon} {text}", command=command, style="Custom.TButton")
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky=(tk.W, tk.E))
            ToolTip(btn, tooltip)
        left_buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        center_buttons_frame = tk.Frame(controls_main_frame, bg=BACKGROUND_COLOR)
        center_buttons_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=20)
        play_buttons = [
            ("播放/暂停", "▶", self.toggle_playback, "播放或暂停当前任务"),
            ("停止", "⏹", self.stop_task, "停止播放"),
        ]
        self.play_buttons_ref = {}
        for i, (text, icon, command, tooltip) in enumerate(play_buttons):
            btn = ttk.Button(center_buttons_frame, text=f"{icon} {text}", command=command, style="Custom.TButton")
            btn.grid(row=0, column=i, padx=5, pady=5, sticky=(tk.W, tk.E))
            self.play_buttons_ref[text] = btn
            ToolTip(btn, tooltip)
        center_buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        right_buttons_frame = tk.Frame(controls_main_frame, bg=BACKGROUND_COLOR)
        right_buttons_frame.grid(row=0, column=2, sticky=(tk.W, tk.E))
        right_buttons = [
            ("上移任务", "⬆", self.move_task_up, "上移选中任务"),
            ("同步时间", "🕒", self.sync_time, "同步系统时间"),
            ("下移任务", "⬇", self.move_task_down, "下移选中任务"),
        ]
        for i, (text, icon, command, tooltip) in enumerate(right_buttons):
            btn = ttk.Button(right_buttons_frame, text=f"{icon} {text}", command=command, style="Custom.TButton")
            btn.grid(row=i, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
            ToolTip(btn, tooltip)
        right_buttons_frame.grid_columnconfigure(0, weight=1)
        
        controls_main_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def setup_status_bar(self):
        """Set up the status bar with enhanced styling."""
        separator = ttk.Separator(self.status_frame, orient="horizontal")
        separator.pack(fill=tk.X)
        status_container = tk.Frame(self.status_frame, bg=BACKGROUND_COLOR)
        status_container.pack(fill=tk.X, padx=10, pady=5)
        
        left_status_frame = tk.Frame(status_container, bg=BACKGROUND_COLOR)
        left_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Add a status icon
        status_icon = tk.Label(left_status_frame, text="ℹ", font=NORMAL_FONT, bg=BACKGROUND_COLOR, fg=PRIMARY_COLOR)
        status_icon.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(left_status_frame, text="就绪", style="Custom.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        right_status_frame = tk.Frame(status_container, bg=BACKGROUND_COLOR)
        right_status_frame.pack(side=tk.RIGHT)
        self.time_label = ttk.Label(right_status_frame, style="Custom.TLabel", width=20)
        self.time_label.pack(side=tk.RIGHT, padx=5)

    def load_tasks(self):
        tasks = load_tasks()
        total_tasks = 0
        for task in tasks:
            self._add_task_to_tree(task)
            total_tasks = len(self.tree.get_children())
        self.status_label.config(text=f"已加载 {total_tasks} 个任务")
        self.check_tasks()

    def _add_task_to_tree(self, task):
        """Add a task to the Treeview with appropriate styling."""
        try:
            if isinstance(task, dict):
                values = [task.get('id', ''), task.get('name', ''), task.get('startTime', ''), task.get('endTime', ''), task.get('volume', ''), task.get('schedule', ''), task.get('audioPath', ''), task.get('status', '等待播放')]
            else:
                values = list(task)
                if len(values) < 8:
                    values.append('等待播放')
            start_time_str = task.get('startTime', '') if isinstance(task, dict) else values[2]
            end_time_str = task.get('endTime', '') if isinstance(task, dict) else values[3]
            schedule_str = task.get('schedule', '') if isinstance(task, dict) else values[5]
            try:
                start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
                end_time = datetime.datetime.strptime(end_time_str, "%H:%M:%S").time()
                now = datetime.datetime.now()
                current_time = now.time()
                current_date = now.strftime("%Y-%m-%d")
                if "," in schedule_str:
                    weekdays = [day.strip() for day in schedule_str.split(",")]
                    current_weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
                    if current_weekday in weekdays:
                        if start_time <= current_time and current_time <= end_time:
                            values[-1] = "正在播放"
                        elif current_time > end_time:
                            values[-1] = "已播放"
                        else:
                            values[-1] = "等待播放"
                    else:
                        values[-1] = "等待播放"
                else:
                    if schedule_str == current_date:
                        if start_time <= current_time and current_time <= end_time:
                            values[-1] = "正在播放"
                        elif current_time >= end_time:
                            values[-1] = "已播放"
                        else:
                            values[-1] = "等待播放"
                    else:
                        values[-1] = "等待播放"
            except ValueError as e:
                logging.warning(f"Invalid time format: {e}")
            if not os.path.exists(values[6]):
                values[-1] = "文件丢失"
                status_tag = 'error'
            else:
                status_tag = 'playing' if values[-1] in ["已播放", "正在播放"] else 'waiting'
            # Add alternate row styling
            row_index = len(self.tree.get_children())
            row_tag = 'oddrow' if row_index % 2 else 'evenrow'
            self.tree.insert("", "end", values=values, tags=(row_tag, status_tag))
        except Exception as e:
            logging.warning(f"Failed to add task: {e}")

    def start_periodic_checks(self):
        self.update_time()
        self.check_tasks()

    def update_time(self):
        current_time = datetime.datetime.now()
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=time_str)
        self.root.after(1000, self.update_time)

    def check_tasks(self):
        try:
            current_time = datetime.datetime.now()
            current_weekday = ["一", "二", "三", "四", "五", "六", "日"][current_time.weekday()]
            current_date = current_time.strftime("%Y-%m-%d")
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                if len(values) < 8 or values[-1] in ["正在播放", "已播放"]:
                    continue
                start_time_str = values[2]
                try:
                    start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
                    now = datetime.datetime.now().time()
                    if start_time <= now and values[-1] != "已播放":
                        self.update_task_status(item, "已播放", 'playing')
                        continue
                except ValueError:
                    logging.warning(f"Invalid start time format: {start_time_str}")
                    continue
                if values[-1] == "已播放":
                    continue
                if self._should_play_task(values, current_time, current_weekday, current_date):
                    if self.current_playing_sound:
                        self.stop_task()
                    self.play_task(item)
                    break
        except Exception as e:
            logging.warning(f"Task check error: {e}")
        finally:
            self.root.after(1000, self.check_tasks)

    def _should_play_task(self, values, current_time, current_weekday, current_date):
        try:
            task_time = values[2]
            task_date = values[5]
            task_time_obj = datetime.datetime.strptime(task_time, "%H:%M:%S").time()
            current_time_obj = current_time.time()
            time_match = (task_time_obj.hour == current_time_obj.hour and task_time_obj.minute == current_time_obj.minute and abs(task_time_obj.second - current_time_obj.second) <= 1)
            if not time_match:
                return False
            if "," in task_date:
                weekdays = [day.strip() for day in task_date.split(",")]
                return current_weekday in weekdays
            else:
                return task_date == current_date
        except Exception as e:
            logging.warning(f"Task validation error: {e}")
            return False

    def play_task(self, item=None, file_path=None, volume=None):
        try:
            if not item and not file_path:
                selected = self.tree.selection()
                if not selected:
                    messagebox.showinfo("提示", "请先选择要播放的文件")
                    return
                item = selected[0]
            if item:
                values = self.tree.item(item)['values']
                file_path = values[6]
                volume = int(values[4])
            
            # Only stop if switching to a new task
            if self.current_playing_sound and item != self.current_playing_item:
                self.stop_task()
            
            success, duration = safe_play_audio(file_path, volume)
            if success:
                self.current_playing_sound = file_path
                self.current_playing_item = item
                self.current_playing_duration = duration
                self.paused = False
                pygame.mixer.music.play()
                self.update_task_status(item, "正在播放", 'playing')
                self.play_buttons_ref["停止"].config(state="normal")
                self.play_buttons_ref["播放/暂停"].config(text="⏸ 暂停")
                self.stop_thread = False
                self.playing_thread = threading.Thread(target=self.update_play_progress)
                self.playing_thread.daemon = True
                self.playing_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")
            if item:
                self.update_task_status(item, "播放失败", 'error')

    def stop_task(self):
        if self.current_playing_sound:
            self.stop_thread = True
            if self.playing_thread:
                self.playing_thread.join()
            pygame.mixer.music.stop()
            self.update_task_status(self.current_playing_item, "等待播放", 'waiting')
            self.current_playing_sound = ""
            self.current_playing_item = None
            self.paused = False
            self.play_buttons_ref["停止"].config(state="disabled")
            self.play_buttons_ref["播放/暂停"].config(text="▶ 播放/暂停")
            if self.current_time:
                self.current_time.config(text="00:00")
            if self.total_time:
                self.total_time.config(text="/ 00:00")
            self.status_label.config(text="就绪")

    def pause_task(self):
        if self.current_playing_sound and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            self.current_playing_position = pygame.mixer.music.get_pos()
            self.update_task_status(self.current_playing_item, "已暂停", 'paused')
            self.play_buttons_ref["播放/暂停"].config(text="▶ 继续")

    def update_play_progress(self):
        try:
            while not self.stop_thread:
                if pygame.mixer.music.get_busy() and not self.paused:
                    current_position = pygame.mixer.music.get_pos() / 1000
                    elapsed = current_position
                    progress = min((elapsed / self.current_playing_duration) * 100, 100)
                    self.root.after(0, self._update_progress_ui, elapsed, progress)
                elif not pygame.mixer.music.get_busy() and not self.paused and self.current_playing_sound:
                    # Playback completed naturally
                    self.root.after(0, self._on_playback_complete)
                    break
                time.sleep(0.1)
            # No stop_task() here unless explicitly stopped
        except Exception as e:
            logging.warning(f"Progress update error: {e}")
            self.root.after(0, self.stop_task)

    def _update_progress_ui(self, elapsed, progress):
        try:
            elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
            total_str = time.strftime('%M:%S', time.gmtime(self.current_playing_duration))
            if self.current_playing_item:
                values = self.tree.item(self.current_playing_item)["values"]
                self.status_label.config(text=f"当前播放文件：{values[1]} ({elapsed_str}/{total_str})")
        except Exception as e:
            logging.warning(f"UI update error: {e}")

    def _on_playback_complete(self):
        if self.current_playing_item:
            self.update_task_status(self.current_playing_item, "已播放", 'waiting')
        self.stop_task()
        self.status_label.config(text="就绪")

    def update_task_status(self, item, status_text, status_tag):
        if item:
            values = list(self.tree.item(item)["values"])
            tags = list(self.tree.item(item)["tags"])
            if len(values) < len(self.columns):
                values.append("")
            values[-1] = status_text
            tags = [tag for tag in tags if tag not in ['playing', 'paused', 'waiting', 'error']]
            tags.append(status_tag)
            self.tree.item(item, values=values, tags=tags)
            self.status_label.config(text=f"当前任务：{values[1]} - {status_text}")

    def add_task(self):
        default_end_time = "08:00:00"
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            if len(values) > 3:
                default_end_time = values[3]
        if not hasattr(self, 'add_task_window') or self.add_task_window is None:
            self.add_task_window = AddTaskWindow(self, default_time=default_end_time)
        else:
            self.add_task_window.window.focus()

    def edit_task(self, event):
        try:
            selected_item = self.tree.selection()[0]
            task_data = self.tree.item(selected_item)['values']
            if not hasattr(self, 'add_task_window') or self.add_task_window is None:
                self.add_task_window = AddTaskWindow(self, task_data=task_data, selected_item=selected_item)
            else:
                self.add_task_window.window.focus()
        except IndexError:
            messagebox.showinfo("提示", "请先选择要编辑的任务")

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的任务")
            return
        if len(selected) > 1:
            confirm = messagebox.askyesno("确认", f"确定要删除选中的 {len(selected)} 个任务吗？")
        else:
            confirm = messagebox.askyesno("确认", "确定要删除选中的任务吗？")
        if confirm:
            for item in selected:
                self.tree.delete(item)
            self.save_all_tasks()
            messagebox.showinfo("成功", f"已删除 {len(selected)} 个任务")

    def copy_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要复制的任务")
            return
        for item in selected:
            values = list(self.tree.item(item)["values"])
            values[1] = f"{values[1]} - 副本"
            if len(values) > 7:
                values = values[:7]
            new_id = len(self.tree.get_children()) + 1
            values[0] = new_id
            self.tree.insert("", "end", values=values)
        self.save_all_tasks()

    def move_task_up(self):
        self._move_task(-1)

    def move_task_down(self):
        self._move_task(1)

    def _move_task(self, direction):
        try:
            selected = self.tree.selection()[0]
            idx = self.tree.index(selected)
            if 0 <= idx + direction < len(self.tree.get_children()):
                self.tree.move(selected, "", idx + direction)
                self.update_task_order()
        except IndexError:
            messagebox.showinfo("提示", "请选择要移动的任务")

    def update_task_order(self):
        tasks = []
        for idx, item in enumerate(self.tree.get_children(), 1):
            values = list(self.tree.item(item)['values'])
            values[0] = idx
            tasks.append(values)
            self.tree.set(item, 0, idx)
        save_all_tasks(tasks)

    def import_tasks(self):
        file_path = filedialog.askopenfilename(title="导入任务", filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")])
        if not file_path:
            return
        try:
            self.status_label.config(text="正在导入...")
            with open(file_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            if messagebox.askyesno("确认", "是否清空现有任务？"):
                for item in self.tree.get_children():
                    self.tree.delete(item)
            total_tasks = len(tasks)
            for task in tasks:
                self._add_task_to_tree(task)
            self.save_all_tasks()
            self.status_label.config(text=f"已导入 {total_tasks} 个任务")
            messagebox.showinfo("成功", f"成功导入 {total_tasks} 个任务")
        except Exception as e:
            self.status_label.config(text="导入失败")
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_tasks(self):
        file_path = filedialog.asksaveasfilename(title="导出任务", defaultextension=".json", filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")])
        if not file_path:
            return
        try:
            tasks = []
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                tasks.append(values[:7])
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", f"成功导出 {len(tasks)} 个任务")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def sync_time(self):
        try:
            result = os.system("w32tm /resync")
            if result == 0:
                messagebox.showinfo("提示", "时间同步成功")
            elif result == 1314:
                messagebox.showerror("错误", "时间同步失败：没有管理员权限")
            else:
                messagebox.showerror("错误", f"时间同步失败，错误代码：{result}")
        except Exception as e:
            messagebox.showerror("错误", f"时间同步失败: {str(e)}")

    def save_all_tasks(self):
        tasks = []
        for item in self.tree.get_children():
            values = list(self.tree.item(item)["values"])
            task_data = {
                "id": values[0],
                "name": values[1],
                "startTime": values[2],
                "endTime": values[3],
                "volume": values[4],
                "schedule": values[5],
                "audioPath": values[6],
                "status": values[7] if len(values) > 7 else "waiting"
            }
            tasks.append(task_data)
        if save_all_tasks(tasks):
            self.status_label.config(text="任务已保存")
        else:
            self.status_label.config(text="保存任务失败")

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            for item in self.tree.get_children():
                tags = list(self.tree.item(item)["tags"])
                if "selected" in tags:
                    tags.remove("selected")
                self.tree.item(item, tags=tags)
            for item in selected:
                tags = list(self.tree.item(item)["tags"])
                if "selected" not in tags:
                    tags.append("selected")
                self.tree.item(item, tags=tags)
            item = selected[0]
            values = self.tree.item(item)["values"]
            self.status_label.config(text=f"已选择任务：{values[1]}")

    def sort_by_column(self, column):
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        if hasattr(self, '_sort_column') and self._sort_column == column:
            items.sort(reverse=not self._sort_reverse)
            self._sort_reverse = not self._sort_reverse
        else:
            items.sort()
            self._sort_reverse = False
        self._sort_column = column
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
            if column != "序号":
                self.tree.set(item, "序号", str(index + 1))
        for col in self.columns:
            if col == column:
                self.tree.heading(col, text=f"{col} {'↓' if self._sort_reverse else '↑'}")
            else:
                self.tree.heading(col, text=col)

    def run(self):
        self.root.mainloop()




