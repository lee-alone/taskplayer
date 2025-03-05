import json
import os
import logging
from typing import List, Dict, Any
from constants import TASK_FILE_PATH

class TaskManager:
    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.load_tasks()

    def load_tasks(self) -> bool:
        """加载任务数据"""
        try:
            if os.path.exists(TASK_FILE_PATH):
                with open(TASK_FILE_PATH, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            return True
        except Exception as e:
            logging.error(f"加载任务失败: {e}")
            return False

    def save_tasks(self) -> bool:
        """保存任务数据"""
        try:
            with open(TASK_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"保存任务失败: {e}")
            return False

    def add_task(self, task: Dict[str, Any]) -> bool:
        """添加任务"""
        try:
            task["id"] = str(len(self.tasks) + 1)
            self.tasks.append(task)
            return self.save_tasks()
        except Exception as e:
            logging.error(f"添加任务失败: {e}")
            return False

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """更新任务"""
        try:
            for i, task in enumerate(self.tasks):
                if task["id"] == task_id:
                    self.tasks[i] = task_data
                    return self.save_tasks()
            return False
        except Exception as e:
            logging.error(f"更新任务失败: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            self.tasks = [t for t in self.tasks if t["id"] != task_id]
            return self.save_tasks()
        except Exception as e:
            logging.error(f"删除任务失败: {e}")
            return False

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取任务"""
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return {}
