import schedule
from clean_trash_bin.clean_trash_bin_main import empty_trash
from music_controller import music_control_main
from translate_export import translate_main
from dialog_box.test_window import start_dialog_box
from OCR_identity import OCR_main
from get_world_time import get_world_time_main
from set_reminder.view import main_window



num = int(input("輸入 1 進到media control，2 translate，3 dialog_box，4 OCR 辨識，5 各國標準時間，6 set_reminder，7 clean_trash_bin："))

if num == 1:
    music_control_main.main()   
elif num == 2:
    translate_main.main()       
elif num == 3:
    start_dialog_box()
elif num == 4:
    OCR_main.main()
elif num == 5:
    get_world_time_main.main()
elif num == 6:
    main_window.main()
elif num == 7:
    empty_trash()
else:
    print("輸入錯誤")