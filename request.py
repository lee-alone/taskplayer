import json
import os
import uuid
from tkinter import filedialog, messagebox

def load_tasks():
    try:
        if not os.path.exists("tasks.json"):
            return []
            
        with open("tasks.json", "r", encoding="utf-8") as f:
            tasks = json.load(f)
            
        # 确保数据完整性
        for task in tasks:
            ensure_task_integrity(task)
            
        return tasks
        
    except Exception as e:
        messagebox.showerror("错误", f"读取任务数据失败: {str(e)}")
        return []

def ensure_task_integrity(task):
    if 'uuid' not in task:
        task['uuid'] = str(uuid.uuid4())
    task['time'] = normalize_time_format(task['time'])
    if 'end_time' not in task:
        task['end_time'] = calculate_end_time(task)

def normalize_time_format(time_str):
    # ...existing code...

def save_tasks(tasks):
    """保存任务数据"""
    try:
        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("错误", f"保存任务失败: {str(e)}")

def import_tasks():
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
            return loaded_tasks
        except Exception as e:
            messagebox.showerror("错误", f"导入文件失败: {e}")
    return []

def export_tasks(tasks):
    filename = filedialog.asksaveasfilename(initialdir=".", title="保存播放列表文件", filetypes=(("JSON Files", "*.json"), ("all files", "*.*"),("JSON Files", "*.json")))
    if not filename.endswith(".json"):
        filename += ".json"
    if filename:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("错误", f"导出文件失败: {str(e)})
