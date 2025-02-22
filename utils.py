import datetime
import pygame

def format_time(hour, minute, second):
    """格式化时间为 HH:MM:SS 格式"""
    return f"{int(hour):02d}:{int(minute):02d}:{int(second):02d}"

def calculate_end_time(task, file_path):
    """计算任务结束时间"""
    try:
        sound = pygame.mixer.Sound(file_path)
        duration = sound.get_length()
        start_time = datetime.datetime.strptime(task['time'], "%H:%M:%S")
        end_time = start_time + datetime.timedelta(seconds=duration)
        return end_time.strftime("%H:%M:%S")
    except Exception:
        return "00:00:00"

def validate_time_format(time_str):
    """验证时间格式"""
    try:
        datetime.datetime.strptime(time_str, "%H:%M:%S")
        return True
    except ValueError:
        return False
