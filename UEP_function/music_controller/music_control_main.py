from PyQt5.QtWidgets import QApplication
from music_controller.music_control_ui import MusicControlUI
import music_controller.play_media as play_media
import sys

def main():
    app = QApplication(sys.argv)  # 正確建立 QApplication
    num = int(input("請輸入撥放代碼："))
    music_name = input("請輸入歌曲：")

    match num:
        case 1:
            window = MusicControlUI(play_media.search_music_file_in_explorer(music_name))
            window.show()
            sys.exit(app.exec_())
        case 2:
            play_media.search_youtube(music_name)
        case 3:
            play_media.search_spotify(music_name)

if __name__ == "__main__":
    main()