import pygame
import threading
import time
import logging
from typing import Optional, Callable
import datetime

class PlayerCore:
    def __init__(self):
        self.current_sound: Optional[str] = None
        self.paused: bool = False
        self.current_duration: float = 0
        self.play_thread: Optional[threading.Thread] = None
        self.stop_flag: bool = False
        self.on_progress: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
        self._lock = threading.Lock()
        self.play_queue = []  # 播放队列
        self.queue_lock = threading.Lock()  # 队列锁
        
        pygame.init()
        pygame.mixer.init()

    def add_to_queue(self, file_path: str, volume: int = 100) -> bool:
        """添加任务到播放队列"""
        with self.queue_lock:
            if file_path not in self.play_queue:
                self.play_queue.append((file_path, volume))
                return True
            return False

    def clear_queue(self):
        """清空播放队列"""
        with self.queue_lock:
            self.play_queue.clear()

    def play(self, file_path: str, volume: int = 100, force_switch: bool = False) -> tuple[bool, float]:
        """播放音频文件，支持强制切换播放"""
        try:
            with self._lock:
                # 如果需要强制切换，先停止当前播放
                if force_switch and pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(volume / 100)
                sound = pygame.mixer.Sound(file_path)
                duration = sound.get_length()
                
                pygame.mixer.music.play()
                self.current_sound = file_path
                self.current_duration = duration
                self.paused = False
                self.stop_flag = False
                
                # 启动进度更新线程
                if self.play_thread and self.play_thread.is_alive():
                    self.stop_flag = True
                    self.play_thread.join(timeout=1.0)
                self.play_thread = threading.Thread(target=self._update_progress, daemon=True)
                self.play_thread.start()
                
                return True, duration
        except Exception as e:
            logging.error(f"播放失败: {e}")
            return False, 0

    def pause(self):
        """暂停播放"""
        with self._lock:
            if self.current_sound and not self.paused and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.paused = True

    def resume(self):
        """恢复播放"""
        with self._lock:
            if self.current_sound and self.paused:
                pygame.mixer.music.unpause()
                self.paused = False

    def stop(self):
        """停止播放"""
        with self._lock:
            if self.current_sound:
                self.stop_flag = True
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                if self.play_thread and self.play_thread.is_alive():
                    self.play_thread.join(timeout=1.0)
                self.current_sound = None
                self.paused = False
                self.current_duration = 0
                self.clear_queue()

    def _update_progress(self):
        """更新播放进度"""
        try:
            while not self.stop_flag and self.current_sound:
                with self._lock:
                    if pygame.mixer.music.get_busy() and not self.paused:
                        current_pos = pygame.mixer.music.get_pos() / 1000
                        progress = min(current_pos / self.current_duration * 100, 100)
                        
                        if self.on_progress:
                            self.on_progress(current_pos, progress)
                            
                    elif not pygame.mixer.music.get_busy() and not self.paused:
                        if self.on_complete:
                            self.on_complete()
                        # 检查队列中是否有下一个任务
                        with self.queue_lock:
                            if self.play_queue:
                                next_file, next_volume = self.play_queue.pop(0)
                                # 开始播放下一个任务
                                self.play(next_file, next_volume)
                        break
                        
                time.sleep(0.1)  # 降低CPU使用率
        except Exception as e:
            logging.error(f"进度更新失败: {e}")
