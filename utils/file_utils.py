import os
import json

def ensure_file_exists(filename, default_content=None):
    """确保文件存在，如果不存在则创建"""
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            if default_content is not None:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            else:
                f.write('[]')
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def load_json_file(filename):
    """加载JSON文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件失败 {filename}: {e}")
        return []

def save_json_file(filename, data):
    """保存数据到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存文件失败 {filename}: {e}")
        return False
