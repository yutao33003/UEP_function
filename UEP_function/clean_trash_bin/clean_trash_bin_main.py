import os
import platform
import subprocess
import shutil

def empty_trash():
    system = platform.system()

    try:
        if system == "Windows":
            result = subprocess.run(
                ["powershell", "-Command", "Clear-RecycleBin -Force"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("回收桶已清空")
            else:
                print("回收桶已清空，但返回非零狀態，忽略")

        elif system == "Darwin":  # macOS
            trash_path = os.path.expanduser("~/.Trash")
            if os.path.exists(trash_path):
                for file in os.listdir(trash_path):
                    file_path = os.path.join(trash_path, file)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            print("macOS 資源回收桶已清空")

        elif system == "Linux":
            trash_paths = [
                os.path.expanduser("~/.local/share/Trash/files"),
                os.path.expanduser("~/.local/share/Trash/info")
            ]
            for path in trash_paths:
                if os.path.exists(path):
                    for file in os.listdir(path):
                        file_path = os.path.join(path, file)
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
            print("Linux 資源回收桶已清空")

        else:
            print(f"不支援的系統：{system}")

    except Exception as e:
        print(f"清理失敗：{e}")

if __name__ == "__main__":
    empty_trash()

