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
        
        pygame.init()
        pygame.mixer.init()

    def play(self, file_path: str, volume: int = 100) -> tuple[bool, float]:
        """播放音频文件"""
        try:
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
                self.play_thread.join()
            self.play_thread = threading.Thread(target=self._update_progress, daemon=True)
            self.play_thread.start()
            
            return True, duration
        except Exception as e:
            logging.error(f"播放失败: {e}")
            return False, 0

    def pause(self):
        """暂停播放"""
        if self.current_sound and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True

    def resume(self):
        """恢复播放"""
        if self.current_sound and self.paused:
            pygame.mixer.music.unpause()
            self.paused = False

    def stop(self):
        """停止播放"""
        if self.current_sound:
            self.stop_flag = True
            pygame.mixer.music.stop()
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join()
            self.current_sound = None
            self.paused = False
            self.current_duration = 0

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
                        break
                        
                time.sleep(0.5)
        except Exception as e:
            logging.error(f"进度更新失败: {e}")
