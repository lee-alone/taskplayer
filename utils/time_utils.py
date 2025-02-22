import datetime

def format_time(hour, minute, second):
    """格式化时间为 HH:MM:SS"""
    try:
        return f"{int(hour):02d}:{int(minute):02d}:{int(second):02d}"
    except ValueError:
        return "00:00:00"

def normalize_time_format(time_str):
    """规范化时间格式为 HH:MM:SS"""
    parts = time_str.split(":")
    if len(parts) == 2:
        return f"{parts[0]}:{parts[1]}:00"
    return time_str

def calculate_end_time(start_time, duration_seconds):
    """计算结束时间"""
    try:
        start = datetime.datetime.strptime(start_time, "%H:%M:%S")
        end = start + datetime.timedelta(seconds=duration_seconds)
        return end.strftime("%H:%M:%S")
    except:
        return "00:00:00"
