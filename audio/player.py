import pygame
import threading
import time
import logging
from typing import Optional, Callable

class AudioPlayer:
    """音频播放适配器,统一管理音频播放状态"""
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self._current_file: Optional[str] = None
        self._is_playing = False
        self._is_paused = False
        self._volume = 100
        self._progress_callback = None
        self._complete_callback = None
        self._lock = threading.Lock()
        
    def play(self, file_path: str, volume: int = 100) -> bool:
        try:
            self.stop() # 播放前先停止
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(volume / 100)
            pygame.mixer.music.play()
            
            self._current_file = file_path
            self._is_playing = True
            self._is_paused = False
            self._volume = volume
            
            return True
        except Exception as e:
            logging.error(f"播放失败: {e}")
            return False
            
    def pause(self):
        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            
    def resume(self):
        if self._is_playing and self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            
    def stop(self):
        if self._is_playing:
            pygame.mixer.music.stop()
            self._is_playing = False
            self._is_paused = False
            self._current_file = None
            pygame.mixer.music.unload()
            
    def set_volume(self, volume: int):
        self._volume = volume
        if self._is_playing:
            pygame.mixer.music.set_volume(volume / 100)
            
    def get_position(self) -> float:
        """获取当前播放位置(秒)"""
        if self._is_playing:
            return pygame.mixer.music.get_pos() / 1000
        return 0
        
    def is_playing(self) -> bool:
        return self._is_playing
        
    def is_paused(self) -> bool:
        return self._is_paused
        
    @property
    def current_file(self) -> Optional[str]:
        return self._current_file
        
    def set_progress_callback(self, callback: Callable[[float], None]):
        self._progress_callback = callback
        
    def set_complete_callback(self, callback: Callable[[], None]):
        self._complete_callback = callback
