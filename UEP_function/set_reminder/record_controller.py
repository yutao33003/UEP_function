from datetime import datetime
import json
import os
from PyQt5.QtCore import QObject   
from PyQt5.QtCore import pyqtSignal

class TaskController(QObject):
    data_changed = pyqtSignal(str)

    def __init__(self, section_key = "reminders", filename="set_reminder/task_record.json"):
        super().__init__()
        self.filename = filename
        self.section_key = section_key

    def load_reminders(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8-sig") as f:  # 這裡改成 utf-8-sig
                return json.load(f)
        return {self.section_key: []}

    def save_reminders(self, data):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_reminder(self, reminder):
        data = self.load_reminders()
        data[self.section_key].append(reminder)
        self.save_reminders(data)
        print("已新增提醒:", reminder["title"])
        self.data_changed.emit(reminder["id"])

    def edit_save_task(self, task_id, new_task_data):
        reminders = self.load_reminders()
        updated = False

        for i, task in enumerate(reminders.get(self.section_key, [])):
            if task.get("id") == task_id:
                reminders[self.section_key][i].update(new_task_data)
                updated = True
                break

        if updated:
            self.save_reminders(reminders)
            self.data_changed.emit(task_id)
            print(f"提醒 '{task_id}' 已更新。")
        else:
            print(f"未找到 ID 為 '{task_id}' 的提醒。")

    def delete_task(self, task_id):
        reminders = self.load_reminders()
        original_count = len(reminders.get(self.section_key, []))
        reminders[self.section_key] = [task for task in reminders.get(self.section_key, []) if task.get("id") != task_id]
        
        if len(reminders[self.section_key]) < original_count:
            self.save_reminders(reminders)
            self.data_changed.emit(task_id)
            print(f"提醒 '{task_id}' 已刪除。")
        else:
            print(f"未找到 ID 為 '{task_id}' 的提醒。")

    def update_finish(self, task_id, new_finish_value=True):
        reminders = self.load_reminders()

        for task in reminders.get(self.section_key, []):
            if task.get("id") == task_id:
                task["finish"] = new_finish_value
                
                break  

        self.save_reminders(reminders)

    def move_expired_reminders(self):
        data = self.load_reminders()
        now = datetime.now()

        still_valid = []
        expired = []

        # 檢查 reminders 裡的項目，搬去 expired 或保留
        for task in data.get("reminders", []):
            end_time_str = task.get("end_time", "")
            if end_time_str:
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
                if end_time < now:
                    expired.append(task)
                    continue
            still_valid.append(task)

        # 檢查 expired_reminders 裡的項目，看看有沒有需要搬回來
        for task in data.get("expired_reminders", []):
            end_time_str = task.get("end_time", "")
            if end_time_str:
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
                if end_time >= now: 
                    still_valid.append(task)
                    continue
            expired.append(task)

        data["reminders"] = still_valid
        data["expired_reminders"] = expired
        self.save_reminders(data)

        print(f"檢查完成，{len(expired)} 個過期任務，{len(still_valid)} 個有效任務。")

class TypeController(QObject):
    data_change = pyqtSignal(str)

    def __init__(self, filename="set_reminder/type_record.json"):
        super().__init__()
        self.filename = filename

    def load_types(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        return {"type": []}

    def save_types(self, data):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_type(self, type_obj):
        data = self.load_types()
        data["type"].append(type_obj)
        self.save_types(data)
        self.data_change.emit(type_obj["id"])

    def delete_type(self, type_id):
        data = self.load_types()
        data["type"] = [t for t in data["type"] if t.get("id") != type_id]
        self.save_types(data)
        self.data_change.emit(type_id)

    def has_same_id(self, reminders):
        print(reminders)
        data = self.load_types()
        types = data.get("type", [])
        type_ids = {t.get("id") for t in types}

        if isinstance(reminders, dict):
            return reminders.get("id") in type_ids

        for r in reminders:
            if r.get("id") in type_ids:
                return True
        return False

    def update_type(self, type_obj):
        data = self.load_types()
        updated = False
        for t in data["type"]:
            if t.get("id") == type_obj.get("id"):
                t.update(type_obj)   # 更新內容
                updated = True
                break
        if updated:
            self.save_types(data)
            self.data_change.emit(type_obj["id"])