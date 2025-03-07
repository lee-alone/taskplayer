from audio_player import AudioPlayer
from admin_utils import is_admin
import sys
import logging
from config_manager import get_task_file_path

def main():
    try:
        task_file_path = get_task_file_path()
        player = AudioPlayer(task_file_path)
        player.run()
    except Exception as e:
        logging.error(f"程序运行错误: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()