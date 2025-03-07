import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import datetime
import pygame
from tkcalendar import Calendar
from constants import TASK_FILE_PATH, TITLE_FONT, NORMAL_FONT, PRIMARY_COLOR, SECONDARY_COLOR

class AddTaskWindow:
    def __init__(self, player, task_data=None, selected_item=None, default_time="08:00:00"):
        import logging
        self.player = player
        self.selected_item = selected_item
        self.default_time = default_time
        self.preview_playing = False
        self.preview_sound = None
        try:
            self.setup_window()
            self.setup_ui(task_data)
            if task_data:
                self.load_task_data(task_data)
        except Exception as e:
            logging.error(f"AddTaskWindow 构造失败: {e}")
            raise  # 抛出异常以便捕获

    def setup_window(self):
        self.window = tk.Toplevel(self.player.root)
        self.window.title("调整任务")
        self.window.geometry("900x600")
        self.window.minsize(900, 600)
        self.window.configure(bg="#f5f6f7")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.transient(self.player.root)
        self.window.grab_set()
        self.center_window()

    def setup_ui(self, task_data):
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_panel = ttk.Frame(self.main_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), expand=True)

        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.setup_task_name(self.left_panel, task_data)
        ttk.Separator(self.left_panel, orient="horizontal").pack(fill=tk.X, pady=15)
        self.setup_date_selection(self.left_panel, task_data)

        self.setup_time_setting(self.right_panel, task_data)
        ttk.Separator(self.right_panel, orient="horizontal").pack(fill=tk.X, pady=15)
        self.setup_file_path(self.right_panel, task_data)
        ttk.Separator(self.right_panel, orient="horizontal").pack(fill=tk.X, pady=15)
        self.setup_volume(self.right_panel, task_data)
        self.setup_buttons(self.right_panel)

    def setup_task_name(self, parent, task_data):
        frame = ttk.LabelFrame(parent, text="任务名称", padding="10")
        frame.pack(fill=tk.X)
        self.task_name_entry = ttk.Entry(frame, font=NORMAL_FONT)
        self.task_name_entry.pack(fill=tk.X, padx=5, pady=5)


    def setup_date_selection(self, parent, task_data=None):
        date_frame = ttk.LabelFrame(parent, text="日期设置", padding="10")
        date_frame.pack(fill=tk.BOTH, expand=True)

        radio_frame = ttk.Frame(date_frame)
        radio_frame.pack(fill=tk.X, padx=5, pady=5)

        self.date_weekday_var = tk.IntVar(value=1)
        rb_width = 20
        ttk.Radiobutton(radio_frame, text="单次日期", variable=self.date_weekday_var,
                       value=0, command=self.show_date, width=rb_width).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(radio_frame, text="每周重复", variable=self.date_weekday_var,
                       value=1, command=self.show_weekday, width=rb_width).pack(side=tk.LEFT, padx=10)

        self.cal_container = ttk.Frame(date_frame)
        self.cal_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.cal = Calendar(self.cal_container, selectmode="day", date_pattern="yyyy-mm-dd",
                          background=PRIMARY_COLOR, foreground="white",
                          headersbackground=SECONDARY_COLOR, headersforeground="white",
                          selectbackground=SECONDARY_COLOR, selectforeground="white",
                          normalbackground="#ffffff", normalforeground="black",
                          weekendbackground="#f0f0f0", weekendforeground="black")
        self.cal.pack(pady=5, fill=tk.BOTH, expand=True)

        self.setup_weekday_selection(date_frame, task_data)

        if task_data:
            date_str = task_data[5]
            if "," in date_str:
                self.date_weekday_var.set(1)
                weekdays = [day.strip() for day in date_str.split(",")]
                for i, day in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
                    self.weekday_vars[i].set(day in weekdays)
                self.show_weekday()
            else:
                self.date_weekday_var.set(0)
                try:
                    self.cal.selection_set(date_str)
                except:
                    pass
                self.show_date()
        else:
            self.show_weekday()

    def setup_weekday_selection(self, parent, task_data):
        self.weekdays_frame = ttk.Frame(parent)
        self.weekdays_frame.pack(fill=tk.X, padx=5, pady=5)

        weekday_label = ttk.Label(self.weekdays_frame, text="选择重复的星期:", font=NORMAL_FONT)
        weekday_label.pack(pady=5)

        checkbutton_frame = ttk.Frame(self.weekdays_frame)
        checkbutton_frame.pack(fill=tk.X, padx=5)

        self.weekday_vars = []
        weekday_grid = ttk.Frame(checkbutton_frame)
        weekday_grid.pack(fill=tk.X, expand=True)

        for i, day in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(weekday_grid, text=day, variable=var)
            cb.grid(row=0, column=i, padx=5)
            self.weekday_vars.append(var)
            if i < 5:  # 勾选工作日（周一到周五）
                var.set(True)

        quick_select_frame = ttk.Frame(self.weekdays_frame)
        quick_select_frame.pack(fill=tk.X, pady=10)

        ttk.Button(quick_select_frame, text="工作日", style="Custom.TButton",
                  command=self.select_workdays).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_select_frame, text="全选", style="Custom.TButton",
                  command=lambda: [var.set(True) for var in self.weekday_vars]).pack(side=tk.LEFT, padx=5)
        ttk.Button(quick_select_frame, text="清除", style="Custom.TButton",
                  command=lambda: [var.set(False) for var in self.weekday_vars]).pack(side=tk.LEFT, padx=5)

        self.weekdays_frame.pack_forget()

    def setup_time_setting(self, parent, task_data=None):
        time_frame = ttk.LabelFrame(parent, text="时间设置", padding="10")
        time_frame.pack(fill=tk.X)

        spinner_frame = ttk.Frame(time_frame)
        spinner_frame.pack(fill=tk.X, padx=5, pady=5)

        time_controls = []
        for unit, max_val in [("时", 23), ("分", 59), ("秒", 59)]:
            control_frame = ttk.Frame(spinner_frame)
            control_frame.pack(side=tk.LEFT, padx=5)
            
            up_btn = ttk.Button(control_frame, text="▲", width=3, style="Toolbutton")
            up_btn.pack(pady=(0, 2))
            
            var = tk.StringVar(value="00")
            entry = ttk.Entry(control_frame, textvariable=var, width=3,
                            justify="center", font=NORMAL_FONT)
            entry.pack()
            
            down_btn = ttk.Button(control_frame, text="▼", width=3, style="Toolbutton")
            down_btn.pack(pady=(2, 0))
            
            ttk.Label(control_frame, text=unit, font=NORMAL_FONT).pack(pady=2)
            
            time_controls.append((var, up_btn, down_btn, max_val))
            
            if unit != "秒":
                ttk.Label(spinner_frame, text=":", font=NORMAL_FONT).pack(side=tk.LEFT)

        self.hour_var, self.minute_var, self.second_var = [x[0] for x in time_controls]

        for var, up_btn, down_btn, max_val in time_controls:
            self.bind_time_controls(var, up_btn, down_btn, max_val)

        if task_data:
            start_time = task_data[2]
            try:
                times = start_time.split(":")
                self.hour_var.set(times[0].zfill(2))
                self.minute_var.set(times[1].zfill(2))
                self.second_var.set(times[2].zfill(2))
            except:
                times = self.default_time.split(":")
                self.hour_var.set(times[0].zfill(2))
                self.minute_var.set(times[1].zfill(2))
                self.second_var.set(times[2].zfill(2))
        else:
            # 获取当前时间
            now = datetime.datetime.now()
            self.hour_var.set(f"{now.hour:02d}")
            self.minute_var.set(f"{now.minute:02d}")
            self.second_var.set(f"{now.second:02d}")

    def setup_file_path(self, parent, task_data=None):
        file_frame = ttk.LabelFrame(parent, text="音频文件", padding="10")
        file_frame.pack(fill=tk.X)

        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.pack(fill=tk.X, padx=5, pady=5)

        self.file_path_entry = ttk.Entry(file_entry_frame, font=NORMAL_FONT)
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(file_entry_frame, text="浏览", style="Custom.TButton",
                              command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)

        if task_data:
            self.file_path_entry.insert(0, task_data[6])

    def setup_volume(self, parent, task_data=None):
        volume_frame = ttk.LabelFrame(parent, text="音量控制", padding="10")
        volume_frame.pack(fill=tk.X)

        volume_control_frame = ttk.Frame(volume_frame)
        volume_control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.volume_scale = ttk.Scale(volume_control_frame, from_=0, to=100, orient="horizontal")
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.volume_label = ttk.Label(volume_control_frame, text="0%", width=5)
        self.volume_label.pack(side=tk.LEFT)

        preview_frame = ttk.Frame(volume_frame)
        preview_frame.pack(fill=tk.X, padx=5, pady=5)

        self.preview_button = ttk.Button(preview_frame, 
                                       text="▶ 预览", 
                                       style="Custom.TButton",
                                       command=self.toggle_preview)
        self.preview_button.pack(side=tk.LEFT, padx=5)

        def update_volume(event=None):
            volume = int(self.volume_scale.get())
            self.volume_label.config(text=f"{volume}%")
            if self.preview_playing and self.preview_sound:
                pygame.mixer.music.set_volume(volume / 100)

        self.volume_scale.bind("<Motion>", update_volume)
        self.volume_scale.bind("<ButtonRelease-1>", update_volume)

        if task_data:
            try:
                volume = int(task_data[4])
            except (ValueError, IndexError):
                volume = 100
            self.volume_scale.set(volume)
            update_volume()
        else:
            self.volume_scale.set(100)
            update_volume()

    def setup_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=15)

        cancel_btn = ttk.Button(button_frame, text="✖ 取消", style="Custom.TButton",
                             command=self.on_closing, width=15)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        save_btn = ttk.Button(button_frame, text="✔ 保存", style="Custom.TButton",
                            command=self.save_task, width=15)
        save_btn.pack(side=tk.RIGHT, padx=5)

    def bind_time_controls(self, var, up_btn, down_btn, max_val):
        def validate_time(value):
            try:
                if value == "": return True
                val = int(value)
                return 0 <= val <= max_val
            except ValueError:
                return False

        def increment(event=None):
            try:
                val = int(var.get())
                val = (val + 1) % (max_val + 1)
                var.set(f"{val:02d}")
            except ValueError:
                var.set("00")

        def decrement(event=None):
            try:
                val = int(var.get())
                val = (val - 1) % (max_val + 1)
                var.set(f"{val:02d}")
            except ValueError:
                var.set("00")

        def on_key(event):
            if event.keysym == "Up":
                increment()
                return "break"
            elif event.keysym == "Down":
                decrement()
                return "break"

        def on_scroll(event):
            if event.delta > 0:
                increment()
            else:
                decrement()
            return "break"

        def on_focus_out(event):
            try:
                val = int(var.get())
                var.set(f"{val:02d}")
            except ValueError:
                var.set("00")

        up_btn.configure(command=increment)
        down_btn.configure(command=decrement)

        entry = up_btn.master.children[list(up_btn.master.children.keys())[1]]
        
        entry.bind("<Up>", on_key)
        entry.bind("<Down>", on_key)
        entry.bind("<MouseWheel>", on_scroll)
        entry.bind("<FocusOut>", on_focus_out)

        vcmd = (entry.register(validate_time), '%P')
        entry.configure(validate="key", validatecommand=vcmd)

    def show_date(self):
        self.weekdays_frame.pack_forget()
        self.cal.pack(in_=self.cal_container, fill=tk.BOTH, expand=True)

    def show_weekday(self):
        self.cal.pack_forget()
        self.weekdays_frame.pack(in_=self.cal_container, fill=tk.BOTH, expand=True)

    def select_workdays(self):
        for i, var in enumerate(self.weekday_vars):
            var.set(i < 5)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg")])
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def toggle_preview(self):
        if not self.preview_playing:
            file_path = self.file_path_entry.get()
            if not file_path or not os.path.exists(file_path):
                messagebox.showerror("错误", "请先选择有效的音频文件")
                return

            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(int(self.volume_scale.get()) / 100)
                pygame.mixer.music.play()
                self.preview_playing = True
                self.preview_button.configure(text="⏹ 停止")
            except Exception as e:
                messagebox.showerror("错误", f"预览失败: {str(e)}")
        else:
            pygame.mixer.music.stop()
            self.preview_playing = False
            self.preview_button.configure(text="▶ 预览")

    def validate_inputs(self):
        errors = []
        
        if not self.task_name_entry.get().strip():
            errors.append("任务名称不能为空")

        file_path = self.file_path_entry.get()
        if not file_path:
            errors.append("请选择音频文件")
        elif not os.path.exists(file_path):
            errors.append("选择的音频文件不存在")
        elif not file_path.lower().endswith(('.mp3', '.wav', '.ogg')):
            errors.append("请选择有效的音频文件(mp3/wav/ogg)")

        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            second = int(self.second_var.get())
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError
        except ValueError:
            errors.append("请输入有效的时间")

        if self.date_weekday_var.get() == 1:  # 星期模式
            if not any(var.get() for var in self.weekday_vars):
                errors.append("请至少选择一个星期")

        if errors:
            raise ValueError("\n".join(errors))

    def save_task(self):
        """保存任务"""
        try:
            self.validate_inputs()
            task_data = self.prepare_task_data()
            
            # 构造完整的任务数据
            task = {
                "id": "0",  # 临时ID,后续会自动分配 
                "name": task_data[0],
                "startTime": task_data[1],
                "endTime": task_data[2], 
                "volume": task_data[3],
                "schedule": task_data[4],
                "audioPath": task_data[5],
                "status": "waiting"
            }

            # 获取当前选中项和任务ID映射
            selected_item = self.selected_item if hasattr(self, 'selected_item') else None
            
            # 保存任务
            if selected_item:
                # 编辑模式
                self.player.tree.item(selected_item, values=[
                    task["id"], task["name"], task["startTime"],
                    task["endTime"], task["volume"], task["schedule"],
                    task["audioPath"], task["status"]
                ])
            else:
                # 新增模式
                new_item = self.player.tree.insert("", "end", values=[
                    task["id"], task["name"], task["startTime"],
                    task["endTime"], task["volume"], task["schedule"],
                    task["audioPath"], task["status"]
                ])
                self.player.task_id_map[new_item] = task["id"]

            # 保存所有任务并重新加载
            self.player.save_all_tasks()
            self.player.load_tasks()  # 重新加载以更新显示
            
            messagebox.showinfo("成功", "任务保存成功！")
            self.on_closing()
            
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            messagebox.showerror("保存失败", f"保存任务时发生错误：\n{str(e)}")

    def prepare_task_data(self):
        file_path = self.file_path_entry.get()
        try:
            sound = pygame.mixer.Sound(file_path)
            duration = sound.get_length()
            start_time = f"{int(self.hour_var.get()):02d}:{int(self.minute_var.get()):02d}:{int(self.second_var.get()):02d}"
            end_time = (datetime.datetime.strptime(start_time, "%H:%M:%S") +
                       datetime.timedelta(seconds=duration)).strftime("%H:%M:%S")
        except (IOError, pygame.error) as e:
            start_time = f"{int(self.hour_var.get()):02d}:{int(self.minute_var.get()):02d}:{int(self.second_var.get()):02d}"
            end_time = (datetime.datetime.strptime(start_time, "%H:%M:%S") +
                       datetime.timedelta(minutes=5)).strftime("%H:%M:%S")

        if self.date_weekday_var.get() == 0:  # 日期模式
            play_date = self.cal.get_date()
            date_str = play_date
        else:  # 星期模式
            weekdays = []
            for i, var in enumerate(self.weekday_vars):
                if var.get():
                    weekdays.append(["一", "二", "三", "四", "五", "六", "日"][i])
            date_str = ", ".join(weekdays)

        return [
            self.task_name_entry.get().strip(),  # 任务名称
            start_time,                          # 开始时间
            end_time,                            # 结束时间
            int(self.volume_scale.get()),        # 音量
            date_str,                            # 播放日期/星期
            file_path                            # 文件路径
        ]

    def save_task_data(self, task_data, selected_item=None):
        """保存任务数据，维护内存中的 task_id_map 并触发排序"""
        try:
            # 构造任务数据，ID 暂时设为 0，等待排序后分配
            new_task = [
                "0",           # 临时 ID，后续由 save_all_tasks 重新分配
                task_data[0],  # 任务名称
                task_data[1],  # 开始时间
                task_data[2],  # 结束时间
                task_data[3],  # 音量
                task_data[4],  # 播放日期/星期
                task_data[5],  # 文件路径
                # "创建任务"      # 默认状态
            ]

            # 更新或插入 Treeview
            if selected_item:
                self.player.tree.item(selected_item, values=new_task)
                # 保留现有 ID，等待重新排序
            else:
                new_item = self.player.tree.insert("", "end", values=new_task)
                self.player.task_id_map[new_item] = "0"  # 临时 ID

            # 调用主程序的保存方法以排序和重新分配 ID
            self.player.save_all_tasks()
            self.player.load_tasks()

        except Exception as e:
            raise Exception(f"保存任务数据失败: {str(e)}")

    def update_task_status_in_tree(self, item, status_text):
        if item:
            values = list(self.player.tree.item(item)["values"])
            tags = list(self.player.tree.item(item)["tags"])
            if len(values) < len(self.player.columns):
                values.append("")
            values[-1] = status_text
            tags = [tag for tag in tags if tag not in ['playing', 'paused', 'waiting', 'error']]
            status_tag = 'playing' if status_text in ["已播放", "正在播放"] else 'waiting'
            tags.append(status_tag)
            self.player.tree.item(item, values=values, tags=tags)
            self.player.status_label.config(text=f"当前任务：{values[1]} - {status_text}")

    def center_window(self):
        parent = self.window.master
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_closing(self):
        if self.preview_playing:
            pygame.mixer.music.stop()
        if self.window.winfo_exists():
            self.window.destroy()
        self.player.add_task_window = None

    def load_task_data(self, task_data):
        self.task_name_entry.insert(0, task_data[1])
        self.volume_scale.set(int(task_data[4]))
        if not self.file_path_entry.get(): # 避免重复插入
            self.file_path_entry.insert(0, task_data[6])
        if "," in task_data[5]:
            self.date_weekday_var.set(1)
            weekdays = [day.strip() for day in task_data[5].split(",")]
            for i, day in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
                self.weekday_vars[i].set(day in weekdays)
            self.show_weekday()
        else:
            self.date_weekday_var.set(0)
            try:
                self.cal.selection_set(task_data[5])
            except:
                pass
            self.show_date()