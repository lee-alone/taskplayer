import os
import sys
import json
import uuid

# 确保项目根目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.time_utils import normalize_time_format
from utils.file_utils import ensure_file_exists

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        """加载任务列表"""
        try:
            tasks = ensure_file_exists("tasks.json", [])
            for task in tasks:
                self._ensure_task_integrity(task)
            self.tasks = tasks
        except Exception as e:
            print(f"加载任务失败: {e}")
            self.tasks = []

    def _ensure_task_integrity(self, task):
        """确保任务数据完整性"""
        if 'uuid' not in task:
            task['uuid'] = str(uuid.uuid4())
        task['time'] = normalize_time_format(task['time'])

    def add_task(self, task):
        """添加新任务"""
        task['uuid'] = str(uuid.uuid4())
        self.tasks.append(task)
        self.save_tasks()

    def update_task(self, index, task):
        """更新现有任务"""
        self.tasks[index] = task
        self.save_tasks()

    def delete_task(self, index):
        """删除任务"""
        del self.tasks[index]
        self.save_tasks()

    def save_tasks(self):
        """保存任务列表"""
        try:
            with open("tasks.json", "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务失败: {e}")
