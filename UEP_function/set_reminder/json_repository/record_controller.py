from collections import defaultdict
from datetime import datetime
import json
import os
from PyQt5.QtCore import QObject   
from PyQt5.QtCore import pyqtSignal

class TaskController(QObject):
    data_changed = pyqtSignal(str)  # emit task id

    def __init__(self, section_key="task", filename="set_reminder/json_repository/task_record.json"):
        super().__init__()
        self.filename = filename
        self.section_key = section_key
        # 快取索引: date -> list of ids
        self.date_index = defaultdict(list)
        # 全部事件快取: id -> reminder dict
        self.event_data = {}
        # 初始化快取
        self._load_cache()

    # ---------- I/O ----------
    def load_reminders(self):
        # 更健壯的讀檔：若檔案不存在、是空檔或解析失敗，都回傳預設結構
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                    if not content or not content.strip():
                        return {self.section_key: []}
                    try:
                        return json.loads(content)
                    except Exception:
                        # 若 JSON 解析失敗，回傳安全的空結構
                        return {self.section_key: []}
            except Exception:
                return {self.section_key: []}
        return {self.section_key: []}

    def save_reminders(self, data):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        # 每次保存後重新建立快取
        self._load_cache()

    # ---------- 快取管理 ----------
    def _load_cache(self):
        """建立 event_data 與 date_index 快取"""
        self.date_index.clear()
        self.event_data.clear()
        data = self.load_reminders()
        for task in data.get(self.section_key, []):
            task_id = task.get("id")
            if not task_id:
                continue
            self.event_data[task_id] = task
            # 建立日期索引
            for date_str in self._get_task_dates(task):
                self.date_index[date_str].append(task_id)

    def _get_task_dates(self, task):
        """取得 task 影響的所有日期（跨多天）"""
        dates = set()
        start_str = task.get("start_time")
        end_str = task.get("end_time")

        try:
            start = datetime.fromisoformat(start_str) if start_str else None
            end = datetime.fromisoformat(end_str) if end_str else None
            if start and end:
                curr = start.date()
                while curr <= end.date():
                    dates.add(curr.isoformat())
                    curr = curr.fromordinal(curr.toordinal() + 1)
            elif start:
                dates.add(start.date().isoformat())
            elif end:
                dates.add(end.date().isoformat())
            elif task.get("date"):
                dates.add(task["date"])
        except Exception:
            pass
        return dates

    # ---------- CRUD ----------
    def add_reminder(self, reminder):
        data = self.load_reminders()
        data[self.section_key].append(reminder)
        self.save_reminders(data)
        print("已新增提醒:", reminder.get("title"))
        self.data_changed.emit(reminder.get("id"))

    def edit_save_task(self, task_id, new_task_data):
        data = self.load_reminders()
        updated = False
        for i, task in enumerate(data.get(self.section_key, [])):
            if task.get("id") == task_id:
                data[self.section_key][i].update(new_task_data)
                updated = True
                break

        if updated:
            self.save_reminders(data)
            self.data_changed.emit(task_id)
            print(f"提醒 '{task_id}' 已更新。")
        else:
            print(f"未找到 ID 為 '{task_id}' 的提醒。")

    def delete_task(self, task_id):
        data = self.load_reminders()
        original_count = len(data.get(self.section_key, []))
        data[self.section_key] = [
            task for task in data.get(self.section_key, [])
            if task.get("id") != task_id
        ]
        if len(data[self.section_key]) < original_count:
            self.save_reminders(data)
            self.data_changed.emit(task_id)
            print(f"提醒 '{task_id}' 已刪除。")
        else:
            print(f"未找到 ID 為 '{task_id}' 的提醒。")

    def update_finish(self, task_id, new_finish_value=True):
        task = self.event_data.get(task_id)
        if task:
            task["finish"] = new_finish_value
            # 保存整份資料
            all_data = {self.section_key: list(self.event_data.values())}
            self.save_reminders(all_data)

    # ---------- 快取查詢 ----------
    def get_events_by_date(self, iso_date):
        """快速取得指定日期的所有事件"""
        task_ids = self.date_index.get(iso_date, [])
        return [self.event_data[tid] for tid in task_ids if tid in self.event_data]

    def get_all_events(self):
        """取得全部事件"""
        return list(self.event_data.values())


class TypeController(QObject):
    data_change = pyqtSignal(str)

    def __init__(self, filename="set_reminder/json_repository/type_record.json"):
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