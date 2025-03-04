from audio_player import AudioPlayer
from admin_utils import is_admin
import sys
import logging

def main():
    try:
        player = AudioPlayer()
        player.run()
    except Exception as e:
        logging.error(f"程序运行错误: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()