import json
import os

CONFIG_FILE = "config.json"
DEFAULT_TASK_FILE = "task.json"


def get_task_file_path():
    """
    从 config.json 文件中读取任务文件路径。
    如果 config.json 文件不存在、为空或路径文件不存在，则返回默认的任务文件路径。
    """
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            task_file_path = config.get("task_file_path")
            if task_file_path and os.path.exists(task_file_path):
                return task_file_path
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        pass  # Handle missing config file or invalid JSON

    return DEFAULT_TASK_FILE


def save_task_file_path(task_file_path):
    """
    将任务文件路径保存到 config.json 文件中。
    """
    config = {"task_file_path": task_file_path}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    # 示例用法
    task_file = get_task_file_path()
    print(f"当前任务文件路径: {task_file}")

    new_task_file_path = "new_task.json"  # 假设用户导入了一个新的任务文件
    save_task_file_path(new_task_file_path)
    print(f"已保存新的任务文件路径: {new_task_file_path}")

    task_file = get_task_file_path()
    print(f"更新后的任务文件路径: {task_file}")