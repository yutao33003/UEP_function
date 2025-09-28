import translate_export.language_map as laguage_map
from translate_export.translate_file import export_file
import winshell

def main():
    origin_file_path = input("輸入要翻譯的檔案路徑：")
    dest_lang = input("輸入要翻譯成甚麼語言：")
    presu_dest_file = winshell.desktop()  # 預設輸出到桌面 
    dest_code = laguage_map.lang_map[dest_lang]
    export_file(dest_code, origin_file_path, presu_dest_file)

if __name__ == "__main__":
    main()