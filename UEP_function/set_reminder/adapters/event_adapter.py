# adapters/event_adapter.py
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import date, datetime
from uuid import uuid4
from typing import List, Dict, Optional

class EventAdapter(QObject):
    """
    把 TaskController 轉成 calendar 可使用的 API。
    - events_updated(str|None) 當某個日期改變或資料變動時會 emit 該日期的 ISO (YYYY-MM-DD)，或 None 表示全域刷新。
    """
    events_updated = pyqtSignal(object)  # emit iso_date string or None

    def __init__(self, task_controller):
        super().__init__()
        self.task_ctrl = task_controller
 
        try:
            self.task_ctrl.data_changed.connect(self._on_taskcontroller_changed)
        except Exception:
            # 如果不是 QObject 或沒有 signal，就忽略連接（保險）
            pass

    # --------- 讀取方法 ----------
    def get_events(self, iso_date: str) -> List[Dict]:
        """
        回傳一個 list，元素為 dict: {id, title, start_time, end_time, finish, raw}
        只會回傳在該 iso_date 當日（date 部分相同）的 events。
        """
        data = self.task_ctrl.load_reminders()
        results = []
        # 假設 reminders 在 data[self.task_ctrl.section_key]
        group = data.get("task", [])
        for task in group: 
            if self._task_matches_date(task, iso_date): # 篩選當天資料
                print(self._normalize_task(task))
                results.append(self._normalize_task(task))
        return results

    def get_all_events(self) -> List[Dict]:
        """若需要一次取所有 event（例如建一個 index）可以用"""
        data = self.task_ctrl.load_reminders()
        group = data.get(self.task_ctrl.section_key, [])
        return [self._normalize_task(t) for t in group]

    def get_future_events(self, from_date: Optional[str] = None) -> List[Dict]:
        """取得指定日期（或今天）之後的所有事件"""
        base = (
            datetime.strptime(from_date, "%Y-%m-%d").date()
            if from_date else date.today()
        )
        data = self.task_ctrl.load_reminders()
        group = data.get(self.task_ctrl.section_key, [])
        results = []

        for task in group:
            start = task.get("start_time")
            if not start:
                continue
            try:
                dt = datetime.strptime(start[:16], "%Y-%m-%d %H:%M")
                if dt.date() >= base:
                    results.append(self._normalize_task(task))
            except Exception:
                continue
        return results

    def get_past_events(self, until_date: Optional[str] = None) -> List[Dict]:
        """取得指定日期（或今天）以前的所有事件"""
        base = (
            datetime.strptime(until_date, "%Y-%m-%d").date()
            if until_date else date.today()
        )
        data = self.task_ctrl.load_reminders()
        group = data.get(self.task_ctrl.section_key, [])
        results = []

        for task in group:
            end = task.get("end_time")
            if not end:
                continue
            try:
                dt = datetime.strptime(end[:16], "%Y-%m-%d %H:%M")
                if dt.date() < base:
                    results.append(self._normalize_task(task))
            except Exception:
                continue
        return results

    def get_event_by_id(self, task_id: str) -> Optional[Dict]:
        """
        根據 task_id 回傳該事件的完整 dict（若找不到則回傳 None）
        """
        data = self.task_ctrl.load_reminders()
        group = data.get(self.task_ctrl.section_key, [])
        for task in group:
            if task.get("id") == task_id:
                return self._normalize_task(task)
        return None


    # --------- 修改方法 ----------
    def add_event(self, event_data: Dict) -> Dict:
        """
        event_data 可以包含 title, start_time, end_time, finish...
        自動從 start_time 取出 iso_date。
        """
        from datetime import datetime
        new_id = event_data.get("id") or str(uuid4())
        reminder = event_data.copy()
        reminder["id"] = new_id

        # 嘗試自動取得 iso_date
        if "start_time" in reminder and reminder["start_time"]:
            iso_date = reminder["start_time"][:10]
        else:
            # 若沒指定 start_time，用今天日期
            iso_date = datetime.now().strftime("%Y-%m-%d")
            reminder["start_time"] = f"{iso_date} 09:00"

        if "end_time" not in reminder or not reminder.get("end_time"):
            reminder["end_time"] = f"{iso_date} 10:00"

        if "finish" not in reminder:
            reminder["finish"] = False

        self.task_ctrl.add_reminder(reminder)
        self.events_updated.emit(iso_date)
        return self._normalize_task(reminder)


    def remove_event(self, event_id: str):
        """
        刪除事件（呼叫 TaskController.delete_task）
        TaskController 會 emit data_changed，adapter 會轉發成 events_updated
        """
        self.task_ctrl.delete_task(event_id)
        # 無法直接知道是哪天被刪，emit None 表示請前端全域刷新或自行查詢
        self.events_updated.emit(None)

    def update_event(self, event_id: str, new_data: Dict):
        """
        編輯事件。假設 TaskController.edit_save_task(task_id, new_task_data)
        new_data 應該只包含要更新的欄位（title/start_time/end_time/finish...)
        """
        self.task_ctrl.edit_save_task(event_id, new_data)
        # 若 new_data 含有時間，嘗試解析並 emit 對應日期
        iso = None
        if new_data.get("start_time"):
            iso = self._extract_iso_date(new_data.get("start_time"))
        elif new_data.get("end_time"):
            iso = self._extract_iso_date(new_data.get("end_time"))
        self.events_updated.emit(iso)

    def mark_finished(self, event_id: str, finished=True):
        # 假設 controller 有 update_finish，用來改 finish，並不發 signal（你可以改 controller）
        self.task_ctrl.update_finish(event_id, finished)
        # emit None -> 前端可以選擇刷新當前日期或全部
        self.events_updated.emit(None)

    # --------- internal helper ----------
    def _task_matches_date(self, task: Dict, iso_date: str) -> bool:
        from datetime import datetime, date

        def parse_datetime(s: str):
            if not s:
                return None
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"):
                try:
                    return datetime.strptime(s.strip(), fmt)
                except Exception:
                    continue
            try:
                return datetime.fromisoformat(s.replace(" ", "T"))
            except Exception:
                return None

        if not task:
            return False

        try:
            target_date = date.fromisoformat(iso_date)
        except ValueError:
            return False

        start_dt = parse_datetime(task.get("start_time"))
        end_dt = parse_datetime(task.get("end_time"))

        # print debug
        print("Checking", task.get("title"), "=>", start_dt, end_dt, "target:", iso_date)

        # 沒有任何時間的情況
        if not start_dt and not end_dt:
            return False

        # 若只有 start，視為單日事件
        if start_dt and not end_dt:
            return start_dt.date() == target_date

        # 若只有 end，視為單日事件
        if end_dt and not start_dt:
            return end_dt.date() == target_date

        # 若兩者都有，允許跨日
        if end_dt < start_dt:
            start_dt, end_dt = end_dt, start_dt
        return start_dt.date() <= target_date <= end_dt.date()


    def _extract_iso_date(self, datetime_str: Optional[str]) -> Optional[str]:
        """
        從可能的時間字串中取出 YYYY-MM-DD（容錯多個格式）
        """
        if not datetime_str:
            return None
        candidates = ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        for fmt in candidates:
            try:
                dt = datetime.strptime(datetime_str, fmt)
                return dt.date().isoformat()
            except Exception:
                continue
        # 若解析失敗，嘗試只取前 10 個字元
        try:
            return datetime_str.strip()[:10]
        except Exception:
            return None

    def _normalize_task(self, task: Dict) -> Dict:
        """把 reminder 的原始結構轉成 calendar 要的標準 dict"""
        return {
            "title": task.get("title") or task.get("name") or "Untitled",
            "id": task.get("id"),
            "type": task.get("type") or task.get("category") or "work",
            "start_time": task.get("start_time") or "",
            "end_time": task.get("end_time") or "",
            "description": task.get("description") or "",
            "priority": task.get("priority") or "medium",
            "alert1": task.get("alert1") or "None",
            "alert2": task.get("alert2") or "None",
            "repeat": bool(task.get("repeat", False)),
            "finish": bool(task.get("finish", False)),
            # 修正：is_new_task 應該從原始資料取或預設 False
            "is_new_task": bool(task.get("is_new_task", False))
        }

    def _on_taskcontroller_changed(self, task_id_or_none):
        """
        TaskController.data_changed 會 emit task id（你 controller 的實作是這樣）。
        我們收到後希望找出該 id 所對應的日期，並 emit events_updated(iso_date)
        若找不到，emit None（讓 UI 決定要不要全域刷新）
        """
        # 嘗試找到該 task 的日期
        try:
            data = self.task_ctrl.load_reminders()
            for t in data.get(self.task_ctrl.section_key, []):
                if t.get("id") == task_id_or_none:
                    # 取 start_time 或 end_time 的日期
                    iso = self._extract_iso_date(t.get("start_time")) or self._extract_iso_date(t.get("end_time"))
                    self.events_updated.emit(iso)
                    return
        except Exception:
            pass
        # fallback: 無法找到或 parse，emit None 表示全域刷新
        self.events_updated.emit(None)
