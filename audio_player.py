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
from utils import safe_play_audio, update_task_in_json, load_tasks, save_all_tasks, set_task_status
from player_core import PlayerCore
from task_manager import TaskManager

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
    def __init__(self, task_file_path=None):
        self.task_file_path = task_file_path
        self.player = PlayerCore()
        self.task_manager = TaskManager()
        self.lock = threading.Lock()
        self.task_id_map = {}  # 初始化 task_id_map
        self.last_date = None  # 用于追踪日期变化
        self.setup_root_window()
        self.init_variables()
        #pygame.init()
        #pygame.mixer.init()
        self.setup_styles()
        self.create_main_layout()
        self.setup_components()
        self.load_tasks()
        self.start_periodic_checks()
        self.setup_shortcuts()

        # 设置回调
        self.player.on_progress = self._update_progress_ui
        self.player.on_complete = self._on_playback_complete

    def setup_shortcuts(self):
        """设置快捷键绑定，并确保按钮使用正确的样式"""
        # 播放/暂停 (Ctrl+P)
        self.root.bind("<Control-p>", self.toggle_playback)
        ToolTip(self.play_buttons_ref["播放/暂停"], "播放或暂停当前任务 (Ctrl+P)")

        # 停止 (Ctrl+S)
        self.root.bind("<Control-s>", self.stop_task)
        ToolTip(self.play_buttons_ref["停止"], "停止播放 (Ctrl+S)")

        # 暂停/恢复今天 (Ctrl+Q)
        self.root.bind("<Control-q>", lambda e: self.toggle_pause_today_task())
        ToolTip(self.play_buttons_ref["暂停今天"], "暂停或恢复今天播放 (Ctrl+Q)")

        # 新增任务 (Ctrl+N)
        self.root.bind("<Control-n>", lambda e: self.add_task())

        # 编辑任务 (Ctrl+E)
        self.root.bind("<Control-e>", self.edit_task)

        # 删除任务 (Del)
        self.root.bind("<Delete>", lambda e: self.delete_task())

        # 复制任务 (Ctrl+C)
        self.root.bind("<Control-c>", lambda e: self.copy_task())


        # 同步时间 (Ctrl+T)
        self.root.bind_all("<Control-t>", lambda e: self.sync_time())

        # 导入任务 (Ctrl+I)
        self.root.bind("<Control-i>", lambda e: self.import_tasks())

        # 导出任务 (Ctrl+O)
        self.root.bind("<Control-o>", lambda e: self.export_tasks())

        # 聚焦 Treeview (Ctrl+L)
        self.root.bind("<Control-l>", lambda e: self.tree.focus_set())

        # 全选任务 (Ctrl+A)
        self.root.bind("<Control-a>", lambda e: self.select_all_tasks())
    def setup_root_window(self):
        self.root = tk.Tk()
        self.root.title("任务播放器")
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.configure(bg=BACKGROUND_COLOR)
        self._set_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        # Add container for shadow effect
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        self.root.focus_force()  # 启动时强制焦点到主窗口
    def init_variables(self):
        """初始化变量，优化资源管理"""
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
        # 添加任务计数器，避免重复计算
        self.task_count = 0
        self.manual_stop = False

    def on_window_close(self):
        """窗口关闭时同时保存到两个文件位置"""
        self.save_all_tasks()  # 这里会同时保存到导入文件和默认文件
        self.root.destroy()

    

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
        
        # 表格基本样式
        style.configure("Treeview", 
                      background=BACKGROUND_COLOR,
                      fieldbackground=BACKGROUND_COLOR,
                      foreground="#37474F",
                      font=NORMAL_FONT,
                      rowheight=30)
        
        # 表头样式
        style.configure("Treeview.Heading",
                      background=PRIMARY_COLOR,
                      foreground="white",
                      font=TITLE_FONT,
                      relief="flat",
                      padding=(10, 5))
        
        # 不同状态的颜色配置
        style.map("Treeview",
                 background=[('selected', PRIMARY_COLOR)],
                 foreground=[('selected', 'white')])
        
        # 设置各种状态的标签样式
        self.status_colors = {
            'playing': {'fg': '#4CAF50', 'bg': '#E8F5E9'},  # 绿色系
            'paused': {'fg': '#FFA000', 'bg': '#FFF3E0'},   # 橙色系
            'waiting': {'fg': '#757575', 'bg': BACKGROUND_COLOR},  # 灰色系
            'error': {'fg': '#F44336', 'bg': '#FFEBEE'},    # 红色系
            'paused_today': {'fg': '#0288D1', 'bg': '#E1F5FE'},  # 蓝色系
            'completed': {'fg': '#9C27B0', 'bg': '#F3E5F5'}  # 紫色系，新增完成状态
        }

        # 配置基本 Custom.TButton 样式
        style.configure("Custom.TButton", font="微软雅黑 10", padding=(8, 4), borderwidth=0, background=PRIMARY_COLOR, foreground="white")
        style.map("Custom.TButton", background=[('active', SECONDARY_COLOR), ('pressed', "#00897B")], foreground=[('active', 'white')])
        
        # 为带有快捷键提示的按钮配置变体样式
        style.configure("Shortcut.TButton", font="微软雅黑 10", padding=(8, 4), background=PRIMARY_COLOR, foreground="white")
        style.map("Shortcut.TButton", background=[('active', SECONDARY_COLOR), ('pressed', "#00897B")], foreground=[('active', 'white')])
        
        style.configure("Horizontal.TProgressbar", background=PRIMARY_COLOR, troughcolor="#f5f5f5", bordercolor="#e0e0e0", lightcolor="#64b5f6", darkcolor=SECONDARY_COLOR)
        style.configure("Custom.TLabel", font=NORMAL_FONT)
        style.configure("Title.TLabel", font=TITLE_FONT)
        style.configure("TSeparator", background="#e0e0e0")
        style.configure("TFrame", background=BACKGROUND_COLOR)
        style.configure("TLabelframe", background=BACKGROUND_COLOR, padding=5)
        style.configure("TLabelframe.Label", font=TITLE_FONT, foreground="#424242")


    def create_main_layout(self):
        """Set up the main layout with fully responsive grid."""
        self.task_frame = ttk.Frame(self.main_frame)
        self.task_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=3)  # Treeview gets more space
        self.main_frame.grid_rowconfigure(1, weight=1)  # Buttons get moderate space
        self.main_frame.grid_rowconfigure(2, weight=1)  # Status bar gets minimal space

    def setup_components(self):
        self.setup_tree()
        self.setup_playback_controls()
        self.setup_status_bar()
        
    def setup_tree(self):
        """設置 Treeview，优化列宽和绑定，支持多选"""
        tree_frame = ttk.Frame(self.task_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        self.columns = ("序号", "任务名称", "开始时间", "结束时间", "音量", "播放日期/星期", "文件路径", "状态")
        column_widths = {"序号": 70, "任务名称": 180, "开始时间": 80, "结束时间": 80, 
                        "音量": 60, "播放日期/星期": 120, "文件路径": 250, "状态": 80}
        
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show="headings", 
                                selectmode="extended", style="Treeview")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths[col], minwidth=50,
                            anchor="center" if col not in ["文件路径", "任务名称"] else "w", stretch=True)
        
        # 配置标签，新增 'paused_today' 状态
        self.tree.tag_configure('playing', foreground='#4CAF50', background='#E8F5E9')
        self.tree.tag_configure('paused', foreground='#FFA000', background='#FFF3E0')
        self.tree.tag_configure('waiting', foreground='#757575')
        self.tree.tag_configure('error', foreground='#F44336', background='#FFEBEE')
        self.tree.tag_configure('paused_today', foreground='#0288D1', background='#E1F5FE')  # 新增暂停今天的状态样式
        self.tree.tag_configure('selected', background='#E3F2FD')
        self.tree.tag_configure('oddrow', background="#F5F7FA")
        self.tree.tag_configure('evenrow', background=BACKGROUND_COLOR)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        self.task_frame.grid_columnconfigure(0, weight=1)
        self.task_frame.grid_rowconfigure(0, weight=1)
        
        self.tree.bind("<Double-1>", self.edit_task)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Up>", lambda e: "break")
        self.tree.bind("<Down>", lambda e: "break")

    def update_task_index_display(self, item, is_playing=False):
        """动态更新任务序号列，简化符号管理"""
        if not item or item not in self.tree.get_children():
            return
        
        try:
            values = list(self.tree.item(item)["values"])
            original_index = str(values[0]).replace("▶ ", "")  # 移除已有符号
            new_index = f"▶ {original_index}" if is_playing else original_index
            self.tree.set(item, "序号", new_index)
        except Exception as e:
            logging.warning(f"更新任务序号失败: {e}")

    def toggle_playback(self, event=None):
        """切换播放/暂停状态"""
        selected = self.tree.selection()
        all_items = self.tree.get_children()
        if not selected or len(selected) == len(all_items):  # 全选时禁用播放
            messagebox.showinfo("提示", "请先选择单个任务进行播放（全选状态下不可播放）")
            return

        item = selected[0]
        values = self.tree.item(item)["values"]

        try:
            if not self.current_playing_sound:  # 无任务播放,开始播放选中任务
                self.play_task(item)
                
            elif self.current_playing_item == item:  # 当前任务,切换暂停/恢复
                if self.paused:
                    # 恢复播放
                    self.player.resume()
                    self.paused = False 
                    self.update_task_status(item, "正在播放", 'playing')
                    self.update_task_index_display(item, is_playing=True)
                    self.play_buttons_ref["播放/暂停"].config(text="⏸ 暂停")
                    self.status_label.config(text=f"正在播放: {values[1]}")
                else:
                    # 暂停播放
                    self.player.pause()
                    self.paused = True
                    self.update_task_status(item, "已暂停", 'paused')
                    self.update_task_index_display(item, is_playing=False)  
                    self.play_buttons_ref["播放/暂停"].config(text="▶ 恢复")
                    
            else:  # 选择了其他任务
                self.stop_task()  # 停止当前播放
                self.play_task(item)  # 播放新选中的任务

        except Exception as e:
            logging.error(f"切换播放状态失败: {e}")
            self.update_task_status(item, "操作失败", 'error')
            self.update_task_index_display(item, is_playing=False)
            messagebox.showerror("错误", f"操作失败: {str(e)}")

    def setup_playback_controls(self):
        """Set up playback control buttons with even distribution and updated styles."""
        controls_main_frame = tk.Frame(self.control_frame, bg=BACKGROUND_COLOR)
        controls_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.control_frame.grid_columnconfigure(0, weight=1)

        # 左侧按钮
        left_buttons_frame = tk.Frame(controls_main_frame, bg=BACKGROUND_COLOR)
        left_buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 20))
        left_buttons = [
            ("新增任务", "🆕", self.add_task, "添加新任务 (Ctrl+N)"),
            ("删除任务", "❌", self.delete_task, "删除选中任务 (Del)"),
            ("复制任务", "📋", self.copy_task, "复制选中任务 (Ctrl+C)"),
            ("同步时间", "🕒", self.sync_time, "同步系统时间 (Ctrl+T)"),
            ("导入任务", "📥", self.import_tasks, "从文件导入任务 (Ctrl+I)"),
            ("导出任务", "📤", self.export_tasks, "导出任务到文件 (Ctrl+O)"),
        ]
        for i, (text, icon, command, tooltip) in enumerate(left_buttons):
            btn = ttk.Button(left_buttons_frame, text=f"{icon} {text} ({tooltip.split('(')[-1]}", style="Shortcut.TButton", command=command)
            btn.grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky=(tk.W, tk.E))
            ToolTip(btn, tooltip)
        left_buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # 中间按钮（播放控制）
        center_buttons_frame = tk.Frame(controls_main_frame, bg=BACKGROUND_COLOR)
        center_buttons_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=20)
        play_buttons = [
            ("播放/暂停", "▶", self.toggle_playback, "播放或暂停当前任务 (Ctrl+P)"),
            ("停止", "⏹", self.stop_task, "停止播放 (Ctrl+S)"),
            ("暂停今天", "⏸", self.toggle_pause_today_task, "暂停/恢复今天播放 (Ctrl+Q)"),  # 修改为切换功能
        ]
        self.play_buttons_ref = {}
        self.play_buttons_ref["播放/暂停"] = ttk.Button(center_buttons_frame, text="▶ 播放/暂停 (Ctrl+P)", style="Shortcut.TButton", command=self.toggle_playback)
        for i, (text, icon, command, tooltip) in enumerate(play_buttons):
            if text == "播放/暂停":
                btn = self.play_buttons_ref["播放/暂停"]
            else:
                btn = ttk.Button(center_buttons_frame, text=f"{icon} {text} ({tooltip.split('(')[-1]}", style="Shortcut.TButton", command=command)
            btn.grid(row=0, column=i, padx=3, pady=3, sticky=(tk.W, tk.E))
            self.play_buttons_ref[text] = btn
            ToolTip(btn, tooltip)
        center_buttons_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # 右侧按钮
        right_buttons_frame = tk.Frame(controls_main_frame, bg=BACKGROUND_COLOR)
        right_buttons_frame.grid(row=0, column=2, sticky=(tk.W, tk.E))
        right_buttons = []
        for i, (text, icon, command, tooltip) in enumerate(right_buttons):
            btn = ttk.Button(right_buttons_frame, text=f"{icon} {text} ({tooltip.split('(')[-1]}", style="Shortcut.TButton", command=command)
            btn.grid(row=i, column=0, padx=3, pady=3, sticky=(tk.W, tk.E))
            ToolTip(btn, tooltip)
        right_buttons_frame.grid_columnconfigure(0, weight=1)

        controls_main_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def sync_time(self, event=None):
        """同步系统时间，带权限检查"""
        try:
            from admin_utils import is_admin, run_as_admin
            import sys
            
            self.status_label.config(text="正在同步时间...")
            
            if not is_admin():
                response = messagebox.askyesno(
                    "权限请求",
                    "同步时间需要管理员权限。\n是否以管理员身份重新启动程序？"
                )
                
                if response:
                    # 保存当前任务状态
                    self.save_all_tasks()
                    # 以管理员权限重启程序
                    success = run_as_admin(sys.argv[0])
                    if success:
                        self.root.destroy()  # 关闭当前实例
                    else:
                        messagebox.showerror("错误", "无法获取管理员权限")
                    return
                else:
                    self.status_label.config(text="时间同步已取消")
                    return
            
            # 已有管理员权限，执行同步
            result = os.system("w32tm /resync")
            
            if result == 0:
                self.status_label.config(text="时间同步成功")
                messagebox.showinfo("提示", "系统时间已成功同步")
            else:
                self.status_label.config(text="时间同步失败")
                messagebox.showerror("错误", f"时间同步失败，错误代码：{result}")
                
        except Exception as e:
            logging.error(f"时间同步失败: {e}")
            self.status_label.config(text="时间同步出错")
            messagebox.showerror("错误", f"时间同步失败: {str(e)}")

    def toggle_pause_today_task(self):
        """切换选定任务的当天暂停/恢复状态"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择任务")
            return
        
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_weekday = ["一", "二", "三", "四", "五", "六", "日"][datetime.datetime.now().weekday()]
        
        # 用于动态更新按钮文本
        all_paused = True
        all_resumed = True
        
        for item in selected:
            values = self.tree.item(item)["values"]
            schedule_str = values[5]  # 播放日期/星期
            
            # 检查是否为今天的任务
            date_match = False
            if "," in schedule_str:  # 星期模式
                date_match = current_weekday in [day.strip() for day in schedule_str.split(",")]
            elif schedule_str == current_date:  # 单次日期模式
                date_match = True
            
            if not date_match:
                continue
            
            current_status = values[-1]
            if current_status == "Pause today":
                # 恢复任务
                if item == self.current_playing_item:
                    self.stop_task()  # 如果正在播放，先停止
                self.update_task_status(item, "等待播放", 'waiting')
                self.status_label.config(text=f"任务 '{values[1]}' 已恢复今天播放")
                all_paused = False
            else:
                # 暂停任务
                if item == self.current_playing_item:
                    self.stop_task()
                self.update_task_status(item, "Pause today", "paused_today")
                self.status_label.config(text=f"任务 '{values[1]}' 已暂停今天播放")
                all_resumed = False
        
        # 更新按钮文本（仅当所有选定任务状态一致时切换）
        if selected:
            if all_paused:
                self.play_buttons_ref["暂停今天"].config(text="⏸ 恢复今天 (Ctrl+Q)")
            elif all_resumed:
                self.play_buttons_ref["暂停今天"].config(text="⏸ 暂停今天 (Ctrl+Q)")
        
        self.save_all_tasks()  # 保存状态

    def setup_status_bar(self):
        """设置状态栏，优化布局和响应性"""
        separator = ttk.Separator(self.status_frame, orient="horizontal")
        separator.pack(fill=tk.X, pady=5)
        
        status_container = tk.Frame(self.status_frame, bg=BACKGROUND_COLOR)
        status_container.pack(fill=tk.X, padx=10, pady=5)
        
        # 左侧状态
        left_status_frame = tk.Frame(status_container, bg=BACKGROUND_COLOR)
        left_status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        status_icon = tk.Label(left_status_frame, text="ℹ", font=NORMAL_FONT, bg=BACKGROUND_COLOR, fg=PRIMARY_COLOR)
        status_icon.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(left_status_frame, text="就绪", style="Custom.TLabel", anchor="w")
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(left_status_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 右侧时间
        right_status_frame = tk.Frame(status_container, bg=BACKGROUND_COLOR)
        right_status_frame.pack(side=tk.RIGHT)
        self.task_file_label = ttk.Label(right_status_frame, style="Custom.TLabel", text=f"当前任务文件: {self.task_file_path or TASK_FILE_PATH}", anchor="e")
        self.task_file_label.pack(side=tk.RIGHT, padx=5)
        self.time_label = ttk.Label(right_status_frame, style="Custom.TLabel", width=25, anchor="e")
        self.time_label.pack(side=tk.RIGHT, padx=5)

    def load_tasks(self):
        """加载任务，优化批量插入性能并按开始时间排序"""
        task_file_path = self.task_file_path or TASK_FILE_PATH
        tasks = load_tasks(task_file_path)
        if not tasks:
            self.status_label.config(text="无任务可加载")
            return

        self.save_all_tasks()
        
        now = datetime.datetime.now()
        current_time = now.time()
        current_date = now.strftime("%Y-%m-%d")
        current_weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
        
        # 暂停 Treeview 更新
        self.tree.configure(displaycolumns=())
        self.tree.delete(*self.tree.get_children())
        self.task_id_map.clear()  # 清空现有映射
        
        total_tasks = 0
        for task in tasks:
            self._add_task_to_tree(task, current_time, current_date, current_weekday)
            total_tasks += 1
        
        # 恢复显示并刷新
        self.tree.configure(displaycolumns=self.columns)
        self.status_label.config(text=f"已加载 {total_tasks} 个任务")

    def _add_task_to_tree(self, task, current_time, current_date, current_weekday):
        """添加任务到 Treeview，优化状态判断并维护 task_id_map"""
        try:
            if isinstance(task, dict):
                values = [task.get('id', ''), task.get('name', ''), task.get('startTime', ''), task.get('endTime', ''), task.get('volume', ''), task.get('schedule', ''), task.get('audioPath', ''), task.get('status', 'waiting')]
            else:
                values = list(task) + ["waiting"] if len(task) < 8 else list(task)

            if len(values) < 8:
                logging.warning(f"任务数据不完整: {task}")
                return

            start_time_str, end_time_str, schedule_str, audio_path = values[2], values[3], values[5], values[6]

            if not os.path.exists(audio_path):
                values[-1] = "文件丢失"
                status_tag = 'error'
            else:
                try:
                    start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
                    end_time = datetime.datetime.strptime(end_time_str, "%H:%M:%S").time()
                    now = datetime.datetime.now()
                    current_datetime = datetime.datetime.combine(now.date(), current_time)
                    start_datetime = datetime.datetime.combine(now.date(), start_time)
                    end_datetime = datetime.datetime.combine(now.date(), end_time)

                    if "," in schedule_str:
                        weekdays = [day.strip() for day in schedule_str.split(",")]
                        scheduled_today = current_weekday in weekdays
                    else:
                        scheduled_today = schedule_str == current_date

                    if not scheduled_today:
                        values[-1] = "等待播放"
                    elif current_datetime < start_datetime:
                        values[-1] = "等待播放"
                    elif start_datetime <= current_datetime <= end_datetime:
                        if values[-1] not in ["正在播放", "Pause today"]:  # 保留 Pause today 状态
                            values[-1] = "等待播放"
                    else:
                        values[-1] = "已播放"

                    status_tag = 'playing' if values[-1] == "正在播放" else 'waiting'
                    if values[-1] == "已播放":
                        status_tag = 'waiting'
                    elif values[-1] == "Pause today":
                        status_tag = 'paused_today'

                except ValueError as e:
                    logging.warning(f"时间格式错误: {e}")
                    values[-1] = "时间格式错误"
                    status_tag = 'error'

            row_index = len(self.tree.get_children())
            row_tag = 'oddrow' if row_index % 2 else 'evenrow'
            new_item = self.tree.insert("", "end", values=values, tags=(row_tag, status_tag))
            self.task_id_map[new_item] = values[0]

        except Exception as e:
            logging.error(f"添加任务失败: {e}")
            pass

    def start_periodic_checks(self):
        """启动定期检查，优化事件调度"""
        self.root.after(0, self.update_time)  # 立即启动时间更新
        self.root.after(0, self.check_tasks)  # 立即启动任务检查

    def update_time(self):
        """更新时间显示，并在新一天重置 'Pause today' 状态"""
        try:
            now = datetime.datetime.now()
            weekday_zh = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.config(text=f"{time_str} {weekday_zh}")
            
            # 检查是否进入新的一天，重置 "Pause today" 状态
            current_date = now.strftime("%Y-%m-%d")
            if not hasattr(self, 'last_date') or self.last_date != current_date:
                self.last_date = current_date
                for item in self.tree.get_children():
                    values = self.tree.item(item)['values']
                    if values[-1] == "Pause today":
                        self.update_task_status(item, "等待播放", 'waiting')
                self.save_all_tasks()
        except Exception as e:
            logging.warning(f"时间更新失败: {e}")
        finally:
            self.root.after(1000, self.update_time)

    def check_tasks(self):
        """定期检查任务，优化调度逻辑"""
        try:
            now = datetime.datetime.now()
            current_time = now.time()
            current_date = now.strftime("%Y-%m-%d")
            current_weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]

            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                current_status = values[-1]
                
                # 跳过特定状态的任务
                if current_status in ["已暂停", "Pause today"]:
                    continue

                start_time_str, schedule_str, audio_path = values[2], values[5], values[6]
                if not os.path.exists(audio_path):
                    self.update_task_status(item, "文件丢失", 'error')
                    continue

                try:
                    # 解析时间
                    start_time = datetime.datetime.strptime(start_time_str, "%H:%M:%S").time()
                    now_time = datetime.datetime.strptime(now.strftime("%H:%M:%S"), "%H:%M:%S").time()
                    
                    # 检查是否是今天的任务
                    is_today = False
                    if "," in schedule_str:  # 每周重复模式
                        weekdays = [day.strip() for day in schedule_str.split(",")]
                        is_today = current_weekday in weekdays
                    else:  # 单次日期模式
                        is_today = schedule_str == current_date
                    
                    # 检查时间是否匹配
                    time_matches = (start_time.hour == now_time.hour and 
                                  start_time.minute == now_time.minute and 
                                  start_time.second == now_time.second)

                    if is_today and time_matches:
                        # 如果当前有其他任务在播放，强制切换
                        if self.current_playing_item and self.current_playing_item != item:
                            old_item = self.current_playing_item
                            self.stop_task()  # 停止当前任务
                            # 更新原任务的状态
                            self.update_task_status(old_item, "等待播放", 'waiting')
                            self.update_task_index_display(old_item, is_playing=False)
                        
                        # 播放新任务
                        self.play_task(item, force_switch=True)

                except ValueError as e:
                    logging.warning(f"任务时间格式无效: {e}")
                    self.update_task_status(item, "时间格式错误", 'error')

        except Exception as e:
            logging.error(f"任务检查失败: {e}")
        finally:
            self.root.after(1000, self.check_tasks)

    def _is_scheduled_today(self, schedule_str, current_date, current_weekday):
        """辅助方法：检查任务是否计划在今天执行"""
        if "," in schedule_str:
            return current_weekday in [day.strip() for day in schedule_str.split(",")]
        return schedule_str == current_date

    def _should_play_task(self, values, current_time, current_weekday, current_date):
        try:
            task_time = values[2]
            task_date = values[5]
            task_time_obj = datetime.datetime.strptime(task_time, "%H:%M:%S").time()
            current_time_obj = current_time.time()
            # 仅比较时分秒，忽略日期
            time_match = (task_time_obj.hour == current_time_obj.hour and
                          task_time_obj.minute == current_time_obj.minute and
                          task_time_obj.second == current_time_obj.second)
            if not time_match:
                return False
            if "," in task_date:
                weekdays = [day.strip() for day in task_date.split(",")]
                return current_weekday in weekdays
            else:
                return task_date == current_date
        except ValueError as e:
            logging.warning(f"Task validation error: {e}")
            return False

    def play_task(self, item=None, force_switch=False):
        """播放任务的统一入口"""
        try:
            if not item:
                selected = self.tree.selection()
                if not selected:
                    messagebox.showinfo("提示", "请先选择要播放的任务")
                    return
                item = selected[0]
            
            values = self.tree.item(item)['values']
            file_path = values[6]
            volume = int(values[4])
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.update_task_status(item, "文件丢失", 'error')
                messagebox.showerror("错误", f"音频文件未找到: {file_path}")
                return

            # 播放音频
            success, duration = self.player.play(file_path, volume, force_switch=force_switch)
            if not success:
                raise Exception("音频加载失败")

            # 更新状态
            self.manual_stop = False
            self.current_playing_sound = file_path
            self.current_playing_item = item
            self.current_playing_duration = duration
            self.paused = False
            
            # 更新UI
            self.update_task_status(item, "正在播放", 'playing')
            self.update_task_index_display(item, is_playing=True)
            self.play_buttons_ref["停止"].config(state="normal")
            self.play_buttons_ref["播放/暂停"].config(text="⏸ 暂停")
            self.status_label.config(text=f"正在播放: {values[1]}")
            
        except Exception as e:
            logging.error(f"播放任务失败: {e}")
            if item:
                self.update_task_status(item, "播放失败", 'error')
                self.update_task_index_display(item, is_playing=False)
            messagebox.showerror("错误", f"播放失败: {str(e)}")

    def stop_task(self, event=None):
        """停止当前播放任务"""
        if not self.current_playing_sound:
            return

        try:
            # 设置手动停止标志
            self.manual_stop = True
            # 停止播放和清空队列
            self.player.stop()
            
            # 更新任务状态
            if self.current_playing_item and self.current_playing_item in self.tree.get_children():
                values = self.tree.item(self.current_playing_item)["values"]
                now = datetime.datetime.now()
                try:
                    start_time = datetime.datetime.strptime(values[2], "%H:%M:%S").time()
                    end_time = datetime.datetime.strptime(values[3], "%H:%M:%S").time()
                    current_time = now.time()
                    status_text = "等待播放" if current_time < end_time else "已播放"
                except ValueError:
                    status_text = "等待播放"
                
                self.update_task_status(self.current_playing_item, status_text, 'waiting')
                self.update_task_index_display(self.current_playing_item, is_playing=False)
            
            # 重置状态
            self.current_playing_sound = None
            self.current_playing_item = None
            self.current_playing_duration = 0
            self.manual_stop = False
            self.paused = False
            
            # 更新UI
            self.play_buttons_ref["停止"].config(state="disabled")
            self.play_buttons_ref["播放/暂停"].config(text="▶ 播放/暂停")
            self.status_label.config(text="就绪")
            self.progress_bar['value'] = 0

        except Exception as e:
            logging.error(f"停止任务失败: {e}")
            self.status_label.config(text="停止任务出错")

    def pause_task(self):
        if self.current_playing_sound and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            self.current_playing_position = pygame.mixer.music.get_pos()
            self.update_task_status(self.current_playing_item, "已暂停", 'paused')
            self.play_buttons_ref["播放/暂停"].config(text="▶ 继续")

    def update_play_progress(self, lock):
        """更新播放进度，优化线程退出和UI刷新"""
        try:
            while not self.stop_thread and self.current_playing_sound and not self.manual_stop:
                with lock:
                    if pygame.mixer.music.get_busy() and not self.paused:
                        # 检查当前播放的任务项是否还存在
                        if not self.current_playing_item or self.current_playing_item not in self.tree.get_children():
                            self.root.after(0, self._on_playback_complete)
                            break
                        
                        current_position = pygame.mixer.music.get_pos() / 1000  # 转换为秒
                        progress = min((current_position / self.current_playing_duration) * 100, 100)
                        self.root.after(0, self._update_progress_ui, current_position, progress)
                    elif not pygame.mixer.music.get_busy() and not self.paused:
                        # 播放自然结束
                        self.root.after(0, self._on_playback_complete)
                        break
                time.sleep(0.5)  # 降低刷新频率到 0.5 秒
        except Exception as e:
            logging.error(f"播放进度更新失败: {e}")
            self.root.after(0, self.stop_task)

    def _update_progress_ui(self, elapsed, progress):
        """更新播放进度UI"""
        try:
            if not self.current_playing_item or self.current_playing_item not in self.tree.get_children():
                return

            elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
            total_str = time.strftime('%M:%S', time.gmtime(self.current_playing_duration))

            try:
                values = self.tree.item(self.current_playing_item)["values"]
                self.status_label.config(text=f"正在播放: {values[1]} ({elapsed_str}/{total_str})")
                self.progress_bar['value'] = progress
            except tk.TclError:
                # 如果任务项已被删除或修改，停止播放
                self.root.after(0, self._on_playback_complete)
        except Exception as e:
            # 仅在调试级别记录这个警告，避免刷屏
            logging.debug(f"UI更新失败: {e}")

    def _on_playback_complete(self):
        """处理播放自然结束"""
        try:
            self.progress_bar['value'] = 0
            if self.current_playing_item and self.current_playing_item in self.tree.get_children():
                try:
                    values = self.tree.item(self.current_playing_item)["values"]
                    self.update_task_status(self.current_playing_item, "已播放", 'waiting')
                    self.update_task_index_display(self.current_playing_item, is_playing=False)
                except tk.TclError:
                    logging.info("正在播放的任务项已被移除")
            
            # 无论是否成功更新状态，都清理播放状态
            self.current_playing_sound = None
            self.current_playing_item = None
            self.paused = False
            if hasattr(self, 'play_buttons_ref'):
                self.play_buttons_ref["停止"].config(state="disabled")
                self.play_buttons_ref["播放/暂停"].config(text="▶ 播放/暂停")
            if hasattr(self, 'status_label'):
                self.status_label.config(text="就绪")
            self.play_buttons_ref["播放/暂停"].config(text="▶ 播放/暂停")
        except Exception as e:
            logging.error(f"播放完成处理失败: {e}")
            # 确保状态被重置
            self.current_playing_sound = None
            self.current_playing_item = None
            self.paused = False
            if hasattr(self, 'status_label'):
                self.status_label.config(text="就绪")


    def update_task_status(self, item, status_text, status_tag):
        """更新任务状态和样式"""
        if not item or item not in self.tree.get_children():
            return
            
        try:
            values = list(self.tree.item(item)["values"])
            tags = list(self.tree.item(item)["tags"])
            
            # 更新状态文本
            if len(values) < len(self.columns):
                values.extend([""] * (len(self.columns) - len(values)))
            values[-1] = status_text
            
            # 更新样式标签
            status_tags = ['playing', 'paused', 'waiting', 'error', 'paused_today', 'completed']
            tags = [tag for tag in tags if tag not in status_tags] + [status_tag]
            
            # 应用样式
            if status_tag in self.status_colors:
                style_dict = self.status_colors[status_tag]
                self.tree.tag_configure(status_tag, 
                                      foreground=style_dict['fg'],
                                      background=style_dict['bg'])
            
            self.tree.item(item, values=values, tags=tags)
            
            # 更新任务数据
            task_id = self.task_id_map.get(item)
            if task_id:
                set_task_status(task_id, status_text)
            
            # 更新状态栏
            task_name = values[1]
            if status_text == "已暂停":
                elapsed = pygame.mixer.music.get_pos() / 1000 if self.current_playing_item == item else 0
                elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
                total_str = time.strftime('%M:%S', time.gmtime(self.current_playing_duration))
                self.status_label.config(text=f"任务: {task_name} ({elapsed_str}/{total_str}) - {status_text}")
            else:
                self.status_label.config(text=f"任务: {task_name} - {status_text}")
                
        except Exception as e:
            logging.error(f"更新任务状态失败: {e}")
            self.status_label.config(text=f"状态更新出错: {str(e)}")

    def add_task(self):
        """添加新任务，优化窗口管理和默认值"""
        try:
            default_end_time = datetime.datetime.now().strftime("%H:%M:%S")
            selected_items = self.tree.selection()
            if selected_items:
                selected_item = selected_items[0]
                values = self.tree.item(selected_item)['values']
                if len(values) > 3:
                    default_end_time = values[3]
            
            # 检查窗口状态并创建新窗口
            if not hasattr(self, 'add_task_window') or self.add_task_window is None or self.add_task_window.window.winfo_exists() == 0:
                self.add_task_window = AddTaskWindow(self, default_time=default_end_time)
                if self.add_task_window is None:
                    raise ValueError("AddTaskWindow 构造失败，返回 None")
                # 在 self.window 上绑定销毁回调
                self.add_task_window.window.protocol("WM_DELETE_WINDOW", self.on_add_task_window_close)
            else:
                # 重置窗口状态，而不是直接复用
                self.add_task_window.on_closing()  # 关闭现有窗口
                self.add_task_window = AddTaskWindow(self, default_time=default_end_time)
                self.add_task_window.window.protocol("WM_DELETE_WINDOW", self.on_add_task_window_close)
        
        except Exception as e:
            logging.error(f"添加任务窗口打开失败: {e}")
            messagebox.showerror("错误", f"无法打开添加任务窗口: {str(e)}")

    def edit_task(self, event=None):
        """编辑选定任务，优化窗口管理和数据传递，支持快捷键调用"""
        try:
            selected = self.tree.selection()
            if not selected:
                messagebox.showinfo("提示", "请先选择要编辑的任务")
                return
            
            item = selected[0]
            task_data = self.tree.item(item)['values']
            
            # 检查窗口状态并创建新窗口
            if not hasattr(self, 'add_task_window') or self.add_task_window is None or self.add_task_window.window.winfo_exists() == 0:
                self.add_task_window = AddTaskWindow(self, task_data=task_data, selected_item=item)
                if self.add_task_window is None:
                    raise ValueError("AddTaskWindow 构造失败，返回 None")
                # 在 self.window 上绑定销毁回调
                self.add_task_window.window.protocol("WM_DELETE_WINDOW", self.on_add_task_window_close)
            else:
                self.add_task_window.window.lift()
                self.add_task_window.window.focus_force()
                if hasattr(self.add_task_window, 'load_task_data'):
                    self.add_task_window.load_task_data(task_data)
        
        except Exception as e:
            logging.error(f"编辑任务窗口打开失败: {e}")
            messagebox.showerror("错误", f"无法打开编辑任务窗口: {str(e)}")

    def on_add_task_window_close(self):
        """窗口关闭时重置 self.add_task_window"""
        if self.add_task_window and self.add_task_window.window.winfo_exists():
            self.add_task_window.window.destroy()
        self.add_task_window = None


    def delete_task(self):
        """删除选定任务，支持多选删除，优化用户交互和状态更新"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的任务")
            return
        
        count = len(selected)
        confirm_text = f"确定要删除选中的 {count} 个任务吗？" if count > 1 else "确定要删除选中的任务吗？"
        if not messagebox.askyesno("确认", confirm_text):
            return
        
        try:
            # 如果删除的任务正在播放，先停止
            for item in selected:
                if item == self.current_playing_item:
                    self.stop_task()
                self.tree.delete(item)
            
            self.save_all_tasks()
            self.status_label.config(text=f"已删除 {count} 个任务")
            messagebox.showinfo("成功", f"已删除 {count} 个任务")
            
        except Exception as e:
            logging.error(f"删除任务失败: {e}")
            messagebox.showerror("错误", f"删除任务失败: {str(e)}")

    def select_all_tasks(self):
        """全选所有任务，不影响计划播放，禁用播放按钮"""
        all_items = self.tree.get_children()
        if all_items:
            self.tree.selection_set(all_items)
            self.status_label.config(text=f"已全选 {len(all_items)} 个任务")
            self.play_buttons_ref["播放/暂停"].config(state="disabled")  # 禁用播放按钮
        else:
            self.status_label.config(text="没有任务可全选")

    def copy_task(self):
        """复制选定任务，优化编号和状态管理"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要复制的任务")
            return
        
        try:
            copied_count = 0
            for item in selected:
                values = list(self.tree.item(item)["values"])
                # 生成新任务名称和ID
                new_name = f"{values[1]} - 副本"
                new_id = len(self.tree.get_children()) + 1
                # 移除播放符号并更新ID
                original_index = str(values[0]).replace("▶ ", "").strip()
                values[0] = new_id
                values[1] = new_name
                # 重置状态为等待
                if len(values) > 7:
                    values[7] = "waiting"
                else:
                    values.append("waiting")
                
                # 插入新任务
                row_index = len(self.tree.get_children())
                row_tag = 'oddrow' if row_index % 2 else 'evenrow'
                self.tree.insert("", "end", values=values, tags=(row_tag, 'waiting'))
                copied_count += 1
            
            self.save_all_tasks()
            self.status_label.config(text=f"已复制 {copied_count} 个任务")
            messagebox.showinfo("成功", f"成功复制 {copied_count} 个任务")
            
        except Exception as e:
            logging.error(f"复制任务失败: {e}")
            self.status_label.config(text="复制任务出错")
            messagebox.showerror("错误", f"复制任务失败: {str(e)}")


    #def _move_task(self, direction):
    #    """移动任务的核心逻辑，优化边界检查和状态更新"""
    #    try:
    #        selected = self.tree.selection()
    #        if not selected:
    #            messagebox.showinfo("提示", "请先选择要移动的任务")
    #            return
    #
    #        item = selected[0]
    #        current_idx = self.tree.index(item)
    #        new_idx = current_idx + direction
    #
    #        if 0 <= new_idx < len(self.tree.get_children()):
    #            self.tree.move(item, "", new_idx)
    #            self.update_task_order()
    #            self.status_label.config(text=f"任务已{'上移' if direction < 0 else '下移'}")
    #            # 保持选择状态
    #            self.tree.selection_set(item)
    #            self.tree.focus(item)
    #        else:
    #            self.status_label.config(text="已到达列表顶部或底部")
    #
    #    except Exception as e:
    #        logging.error(f"移动任务失败: {e}")
    #        self.status_label.config(text="移动任务出错")
    #        messagebox.showerror("错误", f"移动任务失败: {str(e)}")

    def update_task_order(self):
        """更新任务顺序并保存"""
        try:
            tasks = []
            for idx, item in enumerate(self.tree.get_children(), 1):
                values = list(self.tree.item(item)["values"])
                original_index = str(values[0]).replace("▶ ", "").strip()
                if original_index != str(idx):  # 只在序号变化时更新
                    values[0] = idx
                    self.tree.set(item, "序号", idx if not self.current_playing_item == item else f"▶ {idx}")
                tasks.append({
                    "id": values[0],
                    "name": values[1],
                    "startTime": values[2],
                    "endTime": values[3],
                    "volume": values[4],
                    "schedule": values[5],
                    "audioPath": values[6],
                    "status": values[7] if len(values) > 7 else "waiting"
                })
            
            # 直接保存，不排序，保持用户手动调整的顺序
            if save_all_tasks(tasks):  # 调用外部工具函数
                self.status_label.config(text="任务顺序已更新")
            else:
                self.status_label.config(text="更新任务顺序失败")
                
        except Exception as e:
            logging.error(f"更新任务顺序失败: {e}")
            self.status_label.config(text="更新顺序出错")

    def import_tasks(self):
        """从文件导入任务，优化数据验证和用户交互"""
        file_path = filedialog.askopenfilename(title="导入任务", filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")])
        if not file_path:
            return
        
        try:
            self.status_label.config(text="正在导入任务...")
            with open(file_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            
            if not isinstance(tasks, list):
                raise ValueError("文件格式错误：期望JSON数组")
            
            # 验证任务数据
            valid_tasks = []
            for task in tasks:
                if not isinstance(task, (list, dict)) or len(task) < 7:
                    logging.warning(f"跳过无效任务: {task}")
                    continue
                if isinstance(task, dict):
                    required_keys = ["id", "name", "startTime", "endTime", "volume", "schedule", "audioPath"]
                    if not all(key in task for key in required_keys):
                        logging.warning(f"跳过缺少必要字段的任务: {task}")
                        continue
                valid_tasks.append(task)
            
            if not valid_tasks:
                raise ValueError("文件中没有有效的任务数据")
            
            # 询问用户是否清空现有任务
            if self.tree.get_children():
                action = messagebox.askyesnocancel("确认", "是否清空现有任务？\n是：清空并导入\n否：追加导入\n取消：中止")
                if action is None:  # 用户取消
                    self.status_label.config(text="导入已取消")
                    return
                elif action:  # 清空
                    self.tree.delete(*self.tree.get_children())
            
            # 加载任务
            now = datetime.datetime.now()
            current_time = now.time()
            current_date = now.strftime("%Y-%m-%d")
            current_weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
            
            for task in valid_tasks:
                self._add_task_to_tree(task, current_time, current_date, current_weekday)
            
            self.save_all_tasks()
            total_tasks = len(valid_tasks)
            self.task_file_path = file_path
            from config_manager import save_task_file_path
            save_task_file_path(file_path)
            self.status_label.config(text=f"已导入 {total_tasks} 个任务")
            self.task_file_label.config(text=f"当前任务文件: {self.task_file_path or TASK_FILE_PATH}")
            messagebox.showinfo("成功", f"成功导入 {total_tasks} 个任务")
            
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {e}")
            self.status_label.config(text="导入失败")
            messagebox.showerror("错误", f"文件格式错误: {str(e)}")
        except Exception as e:
            logging.error(f"导入任务失败: {e}")
            self.status_label.config(text="导入失败")
            messagebox.showerror("错误", f"导入失败: {str(e)}")

    def export_tasks(self):
        """导出任务到文件，优化数据格式和用户反馈"""
        file_path = filedialog.asksaveasfilename(title="导出任务", defaultextension=".json", 
                                                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")])
        if not file_path:
            return
        
        try:
            tasks = []
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                task_data = {
                    "id": str(values[0]).replace("▶ ", "").strip(),  # 移除播放符号
                    "name": values[1],
                    "startTime": values[2],
                    "endTime": values[3],
                    "volume": values[4],
                    "schedule": values[5],
                    "audioPath": values[6],
                    "status": values[7] if len(values) > 7 else "waiting"
                }
                tasks.append(task_data)
            
            if not tasks:
                messagebox.showinfo("提示", "没有任务可导出")
                self.status_label.config(text="无可导出任务")
                return
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)
            
            total_tasks = len(tasks)
            self.status_label.config(text=f"已导出 {total_tasks} 个任务")
            messagebox.showinfo("成功", f"成功导出 {total_tasks} 个任务到 {os.path.basename(file_path)}")
            
        except Exception as e:
            logging.error(f"导出任务失败: {e}")
            self.status_label.config(text="导出失败")
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def save_all_tasks(self):
        """保存所有任务并确保两个位置都得到更新"""
        try:
            tasks = []
            
            # 收集所有任务数据
            for item in self.tree.get_children():
                values = list(self.tree.item(item)["values"])
                original_index = str(values[0]).replace("▶ ", "").strip()
                task_data = {
                    "id": original_index,
                    "name": values[1],
                    "startTime": values[2],
                    "endTime": values[3],
                    "volume": values[4],
                    "schedule": values[5],
                    "audioPath": values[6],
                    "status": values[7] if len(values) > 7 else "waiting"
                }
                tasks.append(task_data)
            
            # 按开始时间排序
            tasks.sort(key=lambda x: x["startTime"])
            
            # 重新分配ID
            for i, task in enumerate(tasks, 1):
                task["id"] = str(i)
            
            # 保存到两个位置
            success = save_all_tasks(tasks, self.task_file_path)
            
            if success:
                self._refresh_tree_with_tasks(tasks)
                return True
            else:
                self.status_label.config(text="保存任务失败")
                return False
                
        except Exception as e:
            logging.error(f"保存任务失败: {e}")
            self.status_label.config(text=f"保存任务出错: {str(e)}")
            return False

    def _refresh_tree_with_tasks(self, tasks):
        """刷新树形表格显示"""
        try:
            self.tree.configure(displaycolumns=())
            self.tree.delete(*self.tree.get_children())
            self.task_id_map.clear()
            
            for task in tasks:
                values = [
                    task["id"],
                    task["name"],
                    task["startTime"],
                    task["endTime"],
                    task["volume"],
                    task["schedule"],
                    task["audioPath"],
                    task.get("status", "waiting")
                ]
                item = self.tree.insert("", "end", values=values)
                self.task_id_map[item] = task["id"]
            
            self.tree.configure(displaycolumns=self.columns)
            self.status_label.config(text=f"已更新 {len(tasks)} 个任务")
            
        except Exception as e:
            logging.error(f"刷新显示失败: {e}")
            raise

    def on_select(self, event):
        """选择任务时更新状态栏，优化性能，并动态调整暂停/恢复按钮"""
        try:
            selected = self.tree.selection()
            all_items = self.tree.get_children()
            if not selected:
                self.status_label.config(text="就绪")
                self.play_buttons_ref["播放/暂停"].config(state="normal")
                self.play_buttons_ref["暂停今天"].config(text="⏸ 暂停今天 (Ctrl+Q)")  # 默认状态
                return
            
            # 检查选定任务的状态以更新按钮文本
            all_paused = True
            all_resumed = True
            for item in selected:
                values = self.tree.item(item)["values"]
                tags = list(self.tree.item(item)["tags"])
                if "selected" not in tags:
                    tags.append("selected")
                self.tree.item(item, tags=tags)
                self.status_label.config(text=f"已选择任务：{values[1]}")
                
                if values[-1] == "Pause today":
                    all_resumed = False
                else:
                    all_paused = False
            
            # 更新按钮文本
            if all_paused:
                self.play_buttons_ref["暂停今天"].config(text="⏸ 恢复今天 (Ctrl+Q)")
            elif all_resumed:
                self.play_buttons_ref["暂停今天"].config(text="⏸ 暂停今天 (Ctrl+Q)")
            
            # 检查是否全选
            if len(selected) == len(all_items):
                self.play_buttons_ref["播放/暂停"].config(state="disabled")
            else:
                self.play_buttons_ref["播放/暂停"].config(state="normal")
            
            # 移除未选中任务的 selected 标签
            for item in all_items:
                if item not in selected:
                    tags = list(self.tree.item(item)["tags"])
                    if "selected" in tags:
                        tags.remove("selected")
                        self.tree.item(item, tags=tags)
                        
        except Exception as e:
            logging.error(f"选择任务失败: {e}")
            self.status_label.config(text="选择出错")

    def sort_by_column(self, column):
        """按列排序任务，优化序号更新和状态保持"""
        try:
            items = [(self.tree.set(item, column), item) for item in self.tree.get_children()]
            reverse = getattr(self, '_sort_reverse', False)
            if hasattr(self, '_sort_column') and self._sort_column == column:
                items.sort(reverse=not reverse)
                self._sort_reverse = not reverse
            else:
                items.sort()
                self._sort_reverse = False
            self._sort_column = column
            
            # 更新 Treeview
            for index, (_, item) in enumerate(items):
                self.tree.move(item, '', index)
                if column != "序号":
                    is_playing = item == self.current_playing_item and self.current_playing_sound
                    self.tree.set(item, "序号", f"▶ {index + 1}" if is_playing else str(index + 1))
            
            # 更新标题显示排序方向
            for col in self.columns:
                self.tree.heading(col, text=f"{col} {'↓' if self._sort_reverse else '↑'}" if col == column else col)
            
            self.save_all_tasks()
            self.status_label.config(text=f"已按 {column} 排序")
            
        except Exception as e:
            logging.error(f"排序失败: {e}")
            self.status_label.config(text="排序出错")

    def run(self):
        self.root.mainloop()



