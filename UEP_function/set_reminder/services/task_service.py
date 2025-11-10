import dataclasses
import datetime
import time
from PyQt5.QtCore import QObject, pyqtSignal
from set_reminder.model.shared_task_state import SharedTaskState


class TaskService(QObject):
    # use generic object for signal types to avoid PyQt signature issues
    show_editor_requested = pyqtSignal(object, bool, object)  # (state, is_overlay, parent)

    def __init__(self, event_adapter, type_controller):
        super().__init__()
        self.event_adapter = event_adapter
        self.type_controller = type_controller

    def open_task_editor(self, task_id=None, iso_date=None, is_overlay=False, parent=None):
        """
        這個方法只負責「準備 Model」並「發射訊號」。
        """
        print(parent)
        def create_new_task_id(task_type: str):
            timestamp = int(time.time() * 1000)  # 毫秒級時間戳
            return f"{task_type}_{timestamp}"

        # --- 1. 判斷邏輯 (保持不變) ---
        if task_id:
            task_data = self.event_adapter.get_event_by_id(task_id)
            if not task_data:
                return
            task_data.setdefault("is_new_task", False)
        else:
            if iso_date:
                start_time = f"{iso_date} 09:00"
                end_time = f"{iso_date} 10:00"
            else:
                now = datetime.datetime.now()
                start_time = now.strftime("%Y-%m-%d %H:%M")
                end_time = (now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")

            task_data = {
                "id": create_new_task_id(task_type="work"),
                "title": "",
                "type": "work",
                "start_time": start_time,
                "end_time": end_time,
                "description": "",
                "priority": "medium",
                "alert1": "None",
                "alert2": "None",
                "repeat": False,
                "is_new_task": True,
            }

        # --- 2. 建立 "Model" ---
        state = SharedTaskState(**task_data)

        # --- 3. 發射訊號 ---
        self.show_editor_requested.emit(state, is_overlay, parent)

    def save_task(self, state_to_save: SharedTaskState):
        task_dict = dataclasses.asdict(state_to_save)

        if state_to_save.is_new_task:
            # 呼叫 adapter 並取得其回傳（通常會包含實際使用的 id / 欄位）
            state_to_save.is_new_task = False
            task_dict = dataclasses.asdict(state_to_save)
            added = self.event_adapter.add_event(task_dict)

            # 若 adapter 回傳 dict，將重要欄位同步回原本的 SharedTaskState 實例
            if isinstance(added, dict):
                for k, v in added.items():
                    if hasattr(state_to_save, k):
                        try:
                            setattr(state_to_save, k, v)
                        except Exception:
                            # 忽略不能設定的屬性
                            pass

            # 確保原始 state 標記為非新建
            
        else:
            self.event_adapter.update_event(state_to_save.id, task_dict)
            # 即便是更新分支，也把 flag 保險性地設為 False
            state_to_save.is_new_task = False
