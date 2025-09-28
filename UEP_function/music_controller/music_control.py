import os
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import threading
import time


class MusicPlayer:
    def __init__(self, file_path):
       self.song = AudioSegment.from_file(file_path)
       self.song_folder = os.path.dirname(file_path)
       self.playlist = self._load_playlist()
       self.current_index = self.playlist.index(file_path)
       self.play_obj = None
       self.paused = False
       self.is_playing = False
       self.thread = None 
       self.position = 0
       self.loop = False
       self.running = False
       self.lock = threading.Lock()
       self.play_start_time = None  # 用於計算播放時間

    def _load_playlist(self):
        exits = ('.mp3', '.wav', '.flac', '.aac', '.m4a', '.mp4', '.wma')
        files = [os.path.join(self.song_folder, f) for f in (os.listdir(self.song_folder)) if f.lower().endswith(exits)]
        return sorted(files)

    def _update_position_on_pause(self):
        """暂停时更新播放位置"""
        if self.play_start_time is not None:
            elapsed_time = int((time.time() - self.play_start_time) * 1000)
            with self.lock:
                self.position += elapsed_time
            self.play_start_time = None

    def _play_loop(self):
        self.running = True
        while self.running:
            while self.paused and self.running: # 暫停時不播放
                time.sleep(0.1)
                continue
            if not self.running:
                break
            with self.lock:
                segment = self.song[self.position:]
                current_song_finished = len(segment) == 0

            if current_song_finished:
                if self.loop:
                    # 单曲循环：重置到开头继续播放
                    with self.lock:
                        self.position = 0
                    print(f"🔂 單曲循環: {os.path.basename(self.playlist[self.current_index])}")
                    continue
                else:
                    # 尝试播放下一首
                    if self._try_next_song():
                        continue  # 成功切换，继续播放循环
                    else:
                        break

            try:
                self.play_obj = _play_with_simpleaudio(segment)
                self.play_start_time = time.time()
                self.play_obj.wait_done()
                if not self.paused:  # 避免 pause 時錯誤更新位置
                    elapsed_time = int((time.time() - self.play_start_time) * 1000)
                    with self.lock:
                        self.position += elapsed_time
            except Exception as e:
                print(f"播放錯誤: {e}")
                break

        self.is_playing = False
        print("播放结束")

    def _try_next_song(self):
        """尝试播放下一首歌，返回True表示成功，False表示播放列表结束"""
        with self.lock:
            next_index = self.current_index + 1
            
            if next_index >= len(self.playlist):
                print("播放列表播放完毕")
                return False
                
            # 切换到下一首
            self.current_index = next_index
            self.position = 0
            self.song = AudioSegment.from_file(self.playlist[self.current_index])
            
        print(f"🎵 自动播放下一首: {os.path.basename(self.playlist[self.current_index])}")
        return True

    def play(self, start =0):
        if self.paused:
            self.paused = False
            self.is_playing = True
            return
        if not self.thread or not self.thread.is_alive():
            self.paused = False
            self.is_playing = True
            self.position = start
            self.thread = threading.Thread(target=self._play_loop, daemon=True)
            self.thread.start()
            print("▶️ 開始播放")

    def pause(self):
        if self.play_obj and not self.paused:
            self._update_position_on_pause()
            self.play_obj.stop()
            self.paused = True# 儲存進度
            print("⏸️ 暫停播放")

    def stop (self): # 終止
        self.running = False       
        if self.play_obj:
            self.play_obj.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.thread = None
        self.position = 0
        self.paused = False
        self.play_start_time = None
        print("⏹️ 終止播放")

    def jump (self, second):
        new_pos = int(second * 1000)
        if new_pos >= len(self.song):
            print("跳轉位置超過音檔長度")
            return

        with self.lock:
            self.position = new_pos

        # 暫停播放
        self.paused = True
        if self.play_obj and self.play_obj.is_playing():
            self.play_obj.stop()

        # 重新啟動播放
        self.paused = False
        self.play_start_time = time.time()

    def toggle_loop(self):
        self.loop = not self.loop
        status = "開啟" if self.loop else "關閉"
        print(f"🔂 單曲循環已{status}")

    def change_song(self, song_keyword):
        from music_controller.play_media import search_music_file_in_explorer
        self.stop()
        file_path = search_music_file_in_explorer(song_keyword)
        if file_path:
            self.current_index = self.playlist.index(file_path)
            self.song = AudioSegment.from_file(file_path)  # 替換音訊
            self.position = 0
            self.thread = None
            self.running = False
            self.paused = False
            self.play()
        else:
            print("❌ 找不到指定歌曲")
     
    def next_song(self):
        with self.lock:
            self.position = 0
            self.current_index += 1
            if self.current_index >= len(self.playlist):
                if self.loop:
                    self.current_index = 0
                else:
                    print("播放完畢")
                    self.stop()
                    return
            self.song = AudioSegment.from_file(self.playlist[self.current_index])

        # 停止當前播放
        if self.play_obj and self.play_obj.is_playing():
            self.play_obj.stop()

        # _play_loop 會自動從 position 0 播放新歌
        self.paused = False
        self.play_start_time = time.time()

        song_name = os.path.basename(self.playlist[self.current_index])
        print(f"⏭️ 下一首: {song_name}")

    def previous_song(self):
        with self.lock:
            self.position = 0
            self.current_index -= 1
            if self.current_index < 0:
                if self.loop:
                    self.current_index = len(self.playlist) - 1
                else:
                    print("已經是第一首歌曲")
                    return
            self.song = AudioSegment.from_file(self.playlist[self.current_index])

        if self.play_obj and self.play_obj.is_playing():
            self.play_obj.stop()

        self.paused = False
        self.play_start_time = time.time()

        song_name = os.path.basename(self.playlist[self.current_index])
        print(f"⏮️ 上一首: {song_name}")
