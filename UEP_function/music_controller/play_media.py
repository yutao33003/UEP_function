import os
import time
import webbrowser
import pywhatkit
from music_controller.music_control import MusicPlayer
import urllib.parse

SEARCH_ROOTS = ["C:/Users", "D:/", "E:/"]
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.flac', '.aac', '.m4a', '.mp4', '.wma')

# 媒體播放器中尋找
def search_music_file_in_explorer(song_keyword):
    for root_dir in SEARCH_ROOTS:
        for folder, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(SUPPORTED_EXTENSIONS) and song_keyword.lower() in file.lower():
                    full_path = os.path.join(folder, file)
                    print(f"找到檔案:{full_path}")
                    return full_path
                    
    print("找不到符合的音樂檔案")
    return None

def play_music(fullpath):
    print(f"Now playing: {fullpath}")
    player = MusicPlayer(fullpath)
    player.play()
    while player.thread.is_alive():
        time.sleep(0.1)
        Instruction = input("請輸入指令 (play, pause, stop, jump [秒數], loop, next, change [歌名]): ")
        if Instruction == "pause":
            player.pause()
        elif Instruction == "stop":
            player.stop()
            break  # 結束播放迴圈
        elif Instruction.startswith("jump "):
            try:
                seconds = float(Instruction.split()[1])
                player.jump(seconds)
            except ValueError:
                print("請輸入有效的數字")
        elif Instruction == "loop":
            player.toggle_loop()
        elif Instruction == "play":
            player.play()
        elif Instruction == "next":
            player.next_song()

        elif Instruction.startswith("change "):
            try:
                song_name = Instruction.split()[1]
                player.change_song(song_name)
            except IndexError:
                print("請輸入有效的歌曲名稱")
        else:
            print("無效的指令")

# youtube 上尋找
def search_youtube(song_name):
    print(f"正在搜尋 YouTube 上的：{song_name}")
    pywhatkit.playonyt(song_name)

# spotify 上搜尋
def search_spotify(song_name):
    query = urllib.parse.quote_plus(song_name)

    try:
        spotify_app_url = f"spotify:search:{query}"
        webbrowser.open(spotify_app_url)
        print("Spotify 應用程式")
    except:
        web_url = f"https://open.spotify.com/search/{query}"
        webbrowser.open(web_url)
        print("Spotify 網頁版")