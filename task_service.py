from typing import List, Optional
from task_model import Task
from config import PathConfig
import json
import logging
import os

class TaskService:
    """任务服务层,处理任务的CRUD操作"""
    
    def __init__(self):
        self.tasks: List[Task] = []
        self.load_tasks()
        
    def load_tasks(self) -> bool:
        try:
            if os.path.exists(PathConfig.TASK_FILE_PATH):
                with open(PathConfig.TASK_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data]
            return True
        except Exception as e:
            logging.error(f"加载任务失败: {e}")
            return False
            
    def save_tasks(self) -> bool:
        try:
            data = [t.to_dict() for t in self.tasks]
            with open(PathConfig.TASK_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"保存任务失败: {e}") 
            return False
            
    def add_task(self, task: Task) -> bool:
        try:
            self.tasks.append(task)
            return self.save_tasks()
        except Exception as e:
            logging.error(f"添加任务失败: {e}")
            return False
            
    def update_task(self, task_id: str, task: Task) -> bool:
        try:
            for i, t in enumerate(self.tasks):
                if t.id == task_id:
                    self.tasks[i] = task
                    return self.save_tasks()
            return False
        except Exception as e:
            logging.error(f"更新任务失败: {e}")
            return False
            
    def delete_task(self, task_id: str) -> bool:
        try:
            self.tasks = [t for t in self.tasks if t.id != task_id]
            return self.save_tasks()
        except Exception as e:
            logging.error(f"删除任务失败: {e}")
            return False
            
    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None