import os
import json
import pygame
from tkinter import messagebox
from constants import TASK_FILE_PATH

def safe_play_audio(file_path, volume=100):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError("音频文件不存在")

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(volume / 100)
        pygame.mixer.music.play()

        # 获取音频时长
        sound = pygame.mixer.Sound(file_path)
        duration = sound.get_length()
        return True, duration

    except Exception as e:
        messagebox.showerror("播放错误", f"播放音频失败: {str(e)}")
        return False, 0

def update_task_in_json(task_data):
    try:
        tasks = []
        if os.path.exists(TASK_FILE_PATH):
            with open(TASK_FILE_PATH, "r", encoding="utf-8") as f:
                try:
                    loaded_tasks = json.load(f)
                    tasks = loaded_tasks if isinstance(loaded_tasks, list) else []
                except json.JSONDecodeError:
                    pass

        # 更新 tasks 列表
        updated = False
        for i, task in enumerate(tasks):
            if task["id"] == task_data["id"]:
                tasks[i] = task_data
                updated = True
                break
        if not updated:
            tasks.append(task_data)

        with open(TASK_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
        return True
    except (IOError, json.JSONDecodeError) as e:
        messagebox.showerror("保存错误", f"保存任务数据失败: {str(e)}")
        return False

def load_tasks(task_file_path=TASK_FILE_PATH):
    if not os.path.exists(task_file_path):
        return []

    try:
        with open(task_file_path, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            return tasks
    except json.JSONDecodeError:
        return []
    except (IOError, json.JSONDecodeError) as e:
        messagebox.showerror("错误", f"加载任务失败: {str(e)}")
        return []

def set_task_status(task_id, status):
    try:
        tasks = []
        if os.path.exists(TASK_FILE_PATH):
            with open(TASK_FILE_PATH, "r", encoding="utf-8") as f:
                try:
                    loaded_tasks = json.load(f)
                    tasks = loaded_tasks if isinstance(loaded_tasks, list) else []
                except json.JSONDecodeError:
                    pass

        # 更新 tasks 列表
        updated = False
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                task["status"] = status
                tasks[i] = task
                updated = True
                break
        
        if not updated:
            return False

        with open(TASK_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
        return True
    except (IOError, json.JSONDecodeError) as e:
        messagebox.showerror("保存错误", f"保存任务数据失败: {str(e)}")
        return False

def save_all_tasks_to_file(tasks, file_path):
    """保存任务到指定文件，确保目录存在"""
    try:
        if file_path:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)
            return True
    except Exception as e:
        logging.error(f"保存任务到文件失败: {e}")
        return False

def save_all_tasks(tasks, imported_file_path=None):
    """同时保存到导入文件和默认文件"""
    try:
        # 先保存到导入的文件（如果存在）
        if imported_file_path:
            if not save_all_tasks_to_file(tasks, imported_file_path):
                return False
                
        # 再保存到默认文件
        if not save_all_tasks_to_file(tasks, TASK_FILE_PATH):
            return False
            
        return True
    except Exception as e:
        logging.error(f"保存任务失败: {e}")
        return False