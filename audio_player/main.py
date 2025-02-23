import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import json
import os
import pygame
from tkcalendar import Calendar

class AudioPlayer:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.current_playing_sound = None
        self.paused = False
        self.setup_ui()
        
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("任务播放器")
        self.setup_main_frame()
        self.setup_tree()
        self.setup_buttons()
        self.setup_time_label()
        self.load_tasks()
        self.update_time()
        
    def setup_main_frame(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def setup_tree(self):
        self.columns = ("序号", "当前状态", "开始时间", "播放日期", "结束时间", "音量", "文件路径")
        self.tree = ttk.Treeview(self.main_frame, columns=self.columns, show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置列标题和列宽
        column_widths = {
            "序号": 50,
            "当前状态": 100,
            "开始时间": 100,
            "播放日期": 150,
            "结束时间": 100,
            "音量": 80,
            "文件路径": 300
        }
        
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col], anchor="center" if col != "文件路径" else "w")
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 添加水平滚动条
        h_scrollbar = ttk.Scrollbar(self.main_frame, orient="horizontal", command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.E, tk.W))
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        # 绑定双击事件
        self.tree.bind("<Double-1>", self.edit_task)
        
        # 调整按钮框架的位置到水平滚动条下方
        self.button_frame_row = 2  # 用于在setup_buttons中引用

    def edit_task(self, event):
        try:
            selected_item = self.tree.selection()[0]
            task_data = self.tree.item(selected_item)['values']
            AddTaskWindow(self, task_data=task_data, selected_item=selected_item)
        except IndexError:
            messagebox.showinfo("提示", "请先选择要编辑的任务")

    def setup_buttons(self):
        self.button_frame = ttk.Frame(self.main_frame, padding="5")
        self.button_frame.grid(row=self.button_frame_row, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        buttons = [
            ("新增任务", self.add_task),
            ("删除任务", self.delete_task),
            ("导入任务", self.import_tasks),
            ("导出任务", self.export_tasks),
            ("排序任务", self.sort_tasks),
            ("播放任务", self.play_task),
            ("暂停任务", self.pause_task),
            ("停止任务", self.stop_task),
            ("同步时间", self.sync_time),
            ("上移任务", self.move_task_up),
            ("下移任务", self.move_task_down)
        ]
        
        for i, (text, command) in enumerate(buttons):
            ttk.Button(self.button_frame, text=text, command=command).grid(
                row=0, column=i, padx=5, pady=5
            )
        
    def setup_time_label(self):
        self.time_label = ttk.Label(self.main_frame, text="")
        self.time_label.grid(row=self.button_frame_row + 1, column=0, columnspan=2, pady=10)
        
    def update_time(self):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def load_tasks(self):
        try:
            with open("audio_player/task.json", "r", encoding="utf-8") as f:
                tasks = json.load(f)
                for task in tasks:
                    if len(task) > 6 and task[6]:  # 处理星期
                        weekday_str = "、".join(task[6].split(","))
                        task[6] = weekday_str
                    # 调整插入顺序
                    values = (task[0], "", task[3], task[1], task[4], task[5], task[2])
                    self.tree.insert("", "end", values=values)
        except FileNotFoundError:
            with open("audio_player/task.json", "w", encoding="utf-8") as f:
                json.dump([], f)
        except json.JSONDecodeError:
            messagebox.showerror("错误", "task.json文件格式错误")

    def add_task(self):
        AddTaskWindow(self)

    def delete_task(self):
        try:
            selected_item = self.tree.selection()[0]
            index = self.tree.index(selected_item)
            self.tree.delete(selected_item)
            
            with open("audio_player/task.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data.pop(index)
                # 重新编号
                for i, task in enumerate(data):
                    task[0] = i + 1
                f.seek(0)
                f.truncate()
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IndexError:
            messagebox.showinfo("提示", "请先选择要删除的任务")

    def play_task(self, item=None, file_path=None, volume=None):
        if not item and not file_path:
            try:
                selected_item = self.tree.selection()[0]
                file_path = self.tree.item(selected_item)['values'][6]
                volume = int(self.tree.item(selected_item)['values'][5])
            except IndexError:
                messagebox.showinfo("提示", "请先选择要播放的任务")
                return
        elif item:
            file_path = self.tree.item(item)['values'][6]
            volume = int(self.tree.item(item)['values'][5])
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            if item:
                self.tree.set(item, "当前状态", "播放失败")
            return
            
        if self.current_playing_sound:
            self.stop_task()
            
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(volume / 100)
            pygame.mixer.music.play()
            self.current_playing_sound = file_path
            self.paused = False
            if item:
                self.tree.set(item, "当前状态", "正在播放")
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")
            if item:
                self.tree.set(item, "当前状态", "播放失败")

    def pause_task(self):
        if self.current_playing_sound:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self._update_playing_status("正在播放")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self._update_playing_status("暂停")

    def _update_playing_status(self, status):
        try:
            for item in self.tree.get_children():
                if self.tree.item(item)['values'][6] == self.current_playing_sound:
                    self.tree.set(item, "当前状态", status)
        except:
            pass

    def stop_task(self):
        if self.current_playing_sound:
            pygame.mixer.music.stop()
            self._update_playing_status("等待播放")
            self.current_playing_sound = None
            self.paused = False

    def sync_time(self):
        try:
            result = os.system("w32tm /resync")
            if result == 0:
                messagebox.showinfo("提示", "时间同步成功")
            elif result == 1114:
                messagebox.showerror("错误", "时间同步失败：没有管理员权限")
            else:
                messagebox.showerror("错误", f"时间同步失败，错误代码：{result}")
        except Exception as e:
            messagebox.showerror("错误", f"时间同步失败: {str(e)}")

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
        with open("audio_player/task.json", "r+", encoding="utf-8") as f:
            data = []
            for idx, item in enumerate(self.tree.get_children(), 1):
                values = self.tree.item(item)['values']
                task = list(values)
                task[0] = idx
                data.append(task)
                self.tree.set(item, 0, idx)
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=4)

    def sort_tasks(self):
        tasks = [(self.tree.set(item, "开始时间"), 
                 self.tree.set(item, "播放日期"), 
                 item) for item in self.tree.get_children()]
        tasks.sort(key=lambda x: (x[1] if x[1] else "9999-99-99", x[0]))
        
        for index, (_, _, item) in enumerate(tasks):
            self.tree.move(item, '', index)
        
        self.update_task_order()

    def import_tasks(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                new_tasks = json.load(f)
                if not isinstance(new_tasks, list):
                    raise ValueError("Invalid task format")
                    
                with open("audio_player/task.json", "r+", encoding="utf-8") as f2:
                    data = json.load(f2) if os.path.getsize("task.json") > 0 else []
                    max_id = max((task[0] for task in data), default=0)
                    
                    for task in new_tasks:
                        if len(task) != 7:
                            messagebox.showerror("错误", f"导入的任务数据格式不正确: {task}")
                            continue
                        max_id += 1
                        task[0] = max_id
                        data.append(task)
                        self.tree.insert("", "end", values=task + [""])
                        
                    f2.seek(0)
                    f2.truncate()
                    json.dump(data, f2, ensure_ascii=False, indent=4)
                    
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_tasks(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if not file_path:
            return
            
        try:
            with open("audio_player/task.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                with open(file_path, "w", encoding="utf-8") as f2:
                    json.dump(data, f2, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def run(self):
        self.root.mainloop()


class AddTaskWindow:
    def __init__(self, player, task_data=None, selected_item=None):
        self.player = player
        self.selected_item = selected_item
        self.window = tk.Toplevel(player.root)
        self.window.title("修改任务" if task_data else "新增任务")
        self.setup_ui(task_data)

    def setup_ui(self, task_data):
        # Task name
        self.setup_task_name(task_data)
        
        # Date/Weekday selection
        self.setup_date_selection()
        
        # Time setting
        self.setup_time_setting()
        
        # File path
        self.setup_file_path()
        
        # Volume
        self.setup_volume()
        
        # Buttons
        self.setup_buttons()
    def setup_task_name(self, task_data):
        tk.Label(self.window, text="任务名称:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.task_name_entry = tk.Entry(self.window)
        self.task_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=2)
        if task_data:
            # 假设任务名称在task_data的某个位置，这里需要根据实际情况修改
            self.task_name_entry.insert(0, task_data[0])

    def setup_date_selection(self, task_data=None):
        self.date_frame = tk.Frame(self.window)
        self.date_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

        self.date_weekday_var = tk.IntVar(value=0)
        ttk.Radiobutton(self.date_frame, text="日期", variable=self.date_weekday_var,
                       value=0, command=self.show_date).grid(row=0, column=1)
        ttk.Radiobutton(self.date_frame, text="星期", variable=self.date_weekday_var,
                       value=1, command=self.show_weekday).grid(row=0, column=2)

        # Calendar
        self.cal = Calendar(self.date_frame, selectmode="day", date_pattern="yyyy-mm-dd")
        self.cal.grid(row=1, column=0, padx=5, pady=5)

        # Weekday selection
        self.setup_weekday_selection(task_data)

        self.show_date()

    def setup_weekday_selection(self, task_data):
        self.weekdays_frame = tk.Frame(self.date_frame)
        self.weekdays_frame.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.weekdays_frame, text="选择星期:").pack()

        self.weekday_vars = []
        for day in ["一", "二", "三", "四", "五", "六", "日"]:
            var = tk.BooleanVar()
            ttk.Checkbutton(self.weekdays_frame, text=day, variable=var).pack(side="left")
            self.weekday_vars.append(var)

        ttk.Button(self.weekdays_frame, text="工作日",
                   command=self.select_workdays).pack()

        self.weekdays_frame.grid_remove()

    def setup_time_setting(self, task_data=None):
        tk.Label(self.window, text="时间设定:").grid(row=2, column=0, padx=5, pady=5, sticky="w")

        time_frame = tk.Frame(self.window)
        time_frame.grid(row=2, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        self.second_var = tk.StringVar(value="00")

        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var,
                    width=3, wrap=True, format="%02.0f").pack(side="left", padx=2)
        tk.Label(time_frame, text=":").pack(side="left")
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var,
                    width=3, wrap=True, format="%02.0f").pack(side="left", padx=2)
        tk.Label(time_frame, text=":").pack(side="left")
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var,
                    width=3, wrap=True, format="%02.0f").pack(side="left", padx=2)

        if task_data:
            self.hour_var.set(task_data[3][:2])
            self.minute_var.set(task_data[3][3:5])
            self.second_var.set(task_data[3][6:8])

    def setup_file_path(self, task_data=None):
        tk.Label(self.window, text="文件路径:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.file_path_entry = tk.Entry(self.window)
        self.file_path_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(self.window, text="浏览", command=self.browse_file).grid(row=3, column=2, padx=5, pady=5)

        if task_data:
            self.file_path_entry.insert(0, task_data[2])

    def setup_volume(self, task_data=None):
        tk.Label(self.window, text="音量:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.volume_scale = ttk.Scale(self.window, from_=0, to=100, orient="horizontal")
        self.volume_scale.set(50)
        self.volume_scale.grid(row=4, column=1, padx=5, pady=5, sticky="ew", columnspan=2)

        if task_data:
            self.volume_scale.set(task_data[5])

    def setup_buttons(self):
        ttk.Button(self.window, text="保存", command=self.save_task).grid(
            row=5, column=1, padx=5, pady=10, sticky="e")
        ttk.Button(self.window, text="取消", command=self.window.destroy).grid(
            row=5, column=2, padx=5, pady=10, sticky="w")

    def show_date(self):
        self.cal.grid()
        self.weekdays_frame.grid_remove()

    def show_weekday(self):
        self.cal.grid_remove()
        self.weekdays_frame.grid()

    def select_workdays(self):
        for i, var in enumerate(self.weekday_vars):
            var.set(i < 5)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3;*.wav;*.ogg")])
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def save_task(self):
        try:
            self.validate_inputs()
            task_data = self.prepare_task_data()
            self.save_task_data(task_data, self.selected_item)
            self.window.destroy()
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    def validate_inputs(self):
        if not self.task_name_entry.get():
            raise ValueError("任务名称不能为空")

        file_path = self.file_path_entry.get()
        if not file_path:
            raise ValueError("请选择文件路径")
        if not os.path.exists(file_path):
            raise ValueError("文件不存在")

        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            second = int(self.second_var.get())
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError
        except ValueError:
            raise ValueError("时间格式错误")

    def prepare_task_data(self):
        file_path = self.file_path_entry.get()

        # Get date or weekdays
        if self.date_weekday_var.get() == 0:
            play_date = self.cal.get_date()
            play_weekdays = []
        else:
            play_date = ""
            play_weekdays = [day for i, day in enumerate(["一", "二", "三", "四", "五", "六", "日"])
                           if self.weekday_vars[i].get()]

        # If neither is selected, use today's date
        if not play_weekdays and not play_date:
            play_date = datetime.datetime.now().strftime("%Y-%m-%d")

        start_time = f"{int(self.hour_var.get()):02d}:{int(self.minute_var.get()):02d}:{int(self.second_var.get()):02d}"

        try:
            sound = pygame.mixer.Sound(file_path)
            duration = sound.get_length()
            end_datetime = (datetime.datetime.strptime(start_time, "%H:%M:%S") +
                          datetime.timedelta(seconds=duration))
            end_time = end_datetime.strftime("%H:%M:%S")
        except:
            end_time = start_time

        volume = int(self.volume_scale.get())

        return [
            self.task_name_entry.get(), # 任务名称
            play_date, # 播放日期
            file_path, # 文件路径
            start_time, # 开始时间
            end_time, # 结束时间
            volume, # 音量
            ",".join(play_weekdays) # 星期
        ]

    def save_task_data(self, task_data, selected_item=None):
        if selected_item:
            # Update display
            self.player.tree.item(selected_item, values=(self.player.tree.item(selected_item)['values'][0],"",task_data[3],task_data[1],task_data[4],task_data[5],task_data[2]))

            # Save to file
            try:
                with open("audio_player/task.json", "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    index = self.player.tree.index(selected_item)
                    data[index] = task_data
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
        else:
            # Update display
            task_data.insert(0,len(self.player.tree.get_children()) + 1)
            self.player.tree.insert("", "end", values=tuple(task_data))

            # Save to file
            try:
                with open("audio_player/task.json", "r+", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
                    data.append(task_data)
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")


if __name__ == "__main__":
    player = AudioPlayer()
    player.run()
