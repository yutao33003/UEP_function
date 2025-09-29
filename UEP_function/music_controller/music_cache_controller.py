import os, json
from turtle import update


CACHE_FILE = "music_controller/music_cache.json"

SEARCH_ROOTS = ["C:/Users", "D:/", "E:/"]
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.flac', '.aac', '.m4a', '.mp4', '.wma')


class MusicCache:
    def __init__(self, extensions=SUPPORTED_EXTENSIONS):
        self.extensions = extensions
        self.data = {"songs": {}, "folders": {}}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8-sig") as f:
                    self.data = json.load(f)
            except Exception:
                print("無法載入歌曲快取")
                self.data = {}

        if "songs" not in self.data:
            self.data["songs"] = {}
        if "folders" not in self.data:
            self.data["folders"] = {}

    def _save_cache(self):
        with open(CACHE_FILE, "w", encoding="utf-8-sig") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def _index_folder(self, folder):
        """把整個資料夾的音樂存進快取"""

        music_files = []
        for file in os.listdir(folder):
            if file.lower().endswith(self.extensions):
                full_path = os.path.join(folder, file)
                self.data["songs"][full_path] = {"name": file, "folder": folder}
                music_files.append(file)
        self.data["folders"][folder] = music_files
        self._save_cache()
        print(f"📂 已索引資料夾 {folder}, 共 {len(music_files)} 首歌")

    def search_song(self, keyword, folder = None):
        """搜尋快取和硬碟的歌"""

        keyword = keyword.lower()

        # 搜尋索引資料夾來找歌
        if folder and folder in self.data["folders"]:
            for file in self.data["folders"][folder]:
                if keyword in file.lower(): 
                    full_path = os.path.join(folder, file)
                    print(f"✅ 在資料夾 {folder} 找到: {full_path}")
                    return full_path  

        song_map = {meta["name"].lower(): full_path for full_path, meta in self.data["songs"].items()}

        # 未傳入folder 時單曲搜尋傳回路徑
        if song_map:
            from rapidfuzz import process
            match, score, _ = process.extractOne(keyword, song_map.keys())
            if score > 70:  
                print(f"✅ 模糊搜尋找到: {song_map[match]} (相似度 {score})")
                return song_map[match]


        # 硬碟搜尋
        search_dirs = [folder] if folder else SEARCH_ROOTS
        for root_dir in search_dirs:
            for folder, _, files in os.walk(root_dir):
                for file in files:
                    if file.lower().endswith(self.extensions) and keyword in file.lower():
                        full_path = os.path.join(folder, file)
                        self._index_folder(folder)
                        print(f"找到檔案:{full_path}")
                        return full_path
                    
        print("找不到符合的音樂檔案")
        return None

    def check_and_update(self):
        """檢查所有快取資料夾是否仍正確，若有變動則更新"""
        updateed = False
        folders_to_remove = []
        
        for folder, cached_files in list(self.data["folders"]):
            if not os.path.exists(folder):
                print(f"⚠️ 資料夾已刪除: {folder}")
                folders_to_remove.append(folder)

                for full_path in list(self.data["songs"].keys()):
                    if self.data["songs"][full_path]["folder"] == folder:
                        del self.data["songs"][full_path]

            else:
                actual_files = [f for f in os.listdir(folder) if f.lower().endswith(self.extensions)]

                # 更新新增檔案
                for file in actual_files:
                    if file not in cached_files:
                        full_path = os.path.join(folder, file)
                        self.data["songs"][full_path] = {"name": file, "folder": folder}
                        cached_files.append(file)
                        print(f"➕ 新增檔案: {full_path}")
                        updated = True

                # 更新刪除檔案
                for file in list(cached_files):
                    if file not in actual_files:
                        full_path = os.path.join(folder, file)
                        if full_path in self.data["songs"]:
                            del self.data["songs"][full_path]
                        cached_files.remove(file)
                        print(f"❌ 移除檔案: {full_path}")
                        updated = True

                self.data["folders"][folder] = cached_files

        for folder in folders_to_remove:
            del self.data["folders"][folder]

        if updated:
            self._save_cache()
            print("✅ 快取已更新")
        else:
            print("✔️ 快取無變動")