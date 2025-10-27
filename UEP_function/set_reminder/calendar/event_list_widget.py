# event_list_widget.py
import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
from set_reminder.animate import gradually_enter_ani
from set_reminder.calendar.calendar_widget import create_date_button_edit
from set_reminder.view.widget.widget import font_setting

class EventListWidget(QWidget):
    add_requested = pyqtSignal(str, object)   # iso date
    remove_requested = pyqtSignal(str, str)  # iso, event_id

    def __init__(self, event_adapter, overlay_controller, type_controller):
        super().__init__()
        self.event_adapter = event_adapter
        self.overlay_controller = overlay_controller
        self.type_controller = type_controller
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.lbl = QLabel("Events")
        cust_font = font_setting(10)
        self.lbl.setFont(cust_font)

        # self.lst 是一個已嵌入的 TypeTaskOverlay 實例（embedded = True）
        # 透過 OverlayController 建立並 cache（scope="calendar"）一次，後續直接使用
        self.lst = self.overlay_controller.show(
            "task_overlay",
            scope="calendar",
            cache=True,
            mode="day",
            task_type="",
            date_filter=datetime.date.today().isoformat(),
            event_adapter=self.event_adapter,
            embedded=True,
            type_controller = self.type_controller,
            parent=self
        )

        h = QHBoxLayout()
        self.btn_add = create_date_button_edit()
        self.btn_add.setText("+")
        self.btn_remove = create_date_button_edit()
        self.btn_remove.setText("Remove")
        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)
        h.addWidget(self.btn_add); h.addWidget(self.btn_remove)
        layout.addWidget(self.lbl)
        layout.addWidget(self.lst)
        gradually_enter_ani(container=self.lst, duration=500)
        layout.addLayout(h)
        self.setLayout(layout)

    def show_events(self, iso_date):
        self.current_date = iso_date
        # 防護呼叫：若 lst 尚未建立或沒有 refresh_data，嘗試重建或 fallback
        if not hasattr(self, "lst") or self.lst is None:
            # 嘗試重建 embedded overlay
            self.lst = self.overlay_controller.show(
                "task_overlay",
                scope="calendar",
                cache=True,
                mode="day",
                task_type="",
                date_filter=iso_date,
                event_adapter=self.event_adapter,
                embedded=True,
                parent=self
            )
            return

        # 若 lst 支援 refresh_data，優先以 child-overlay 方式開 edit（保持 lst 不被替換）
        if hasattr(self.lst, "refresh_data"):
            try:
                self.lst.refresh_data(date_filter=iso_date, mode="day")
            except Exception:
                # fallback：重建 overlay 實體並顯示該日資料
                try:
                    self.lst.close()
                except Exception:
                    pass
                self.lst = self.overlay_controller.show(
                    "task_overlay",
                    scope="calendar",
                    cache=True,
                    mode="day",
                    task_type="",
                    date_filter=iso_date,
                    event_adapter=self.event_adapter,
                    embedded=True,
                    parent=self
                )
        else:
            # 沒有 refresh_data 的情況下，重建 overlay
            try:
                self.lst.close()
            except Exception:
                pass
            self.lst = self.overlay_controller.show(
                "task_overlay",
                scope="calendar",
                cache=True,
                mode="day",
                task_type="",
                date_filter=iso_date,
                event_adapter=self.event_adapter,
                type_controller = self.type_controller,
                embedded=True,
                parent=self
            )

    def _on_add(self):
        if not hasattr(self, "current_date"):
            return
        iso = self.current_date
        # emit 讓 controller 或上層也能處理新增事件
        self.add_requested.emit(iso, self)

        # 重要：若 self.lst 是嵌入的 TypeTaskOverlay，請在它之上開 child overlay（edit_overlay）
        # 這樣就不會關閉或替換嵌入的 overlay（避免 overlay_controller.show 關閉 active_overlay）
        try:
            if hasattr(self, "lst") and self.lst is not None and hasattr(self.lst, "open_child_overlay"):
                # open as child of the embedded overlay so embedded overlay stays visible
                self.lst.open_child_overlay(
                    "edit_overlay",
                    parent=self.lst,
                    task_id="",
                    iso_date=iso,
                    event_adapter=self.event_adapter
                )
                return
        except Exception:
            # 如果失敗再 fallback 到全域顯示
            pass



    def _on_remove(self):
        cur = None
        # 如果 embedded overlay 支援選取項，嘗試從它讀取選中項（兼容不同實作）
        try:
            if hasattr(self.lst, "get_selected_event_id"):
                cur_id = self.lst.get_selected_event_id()
                if cur_id:
                    self.remove_requested.emit(self.current_date, cur_id)
                    return
        except Exception:
            pass

        # fallback 保持原有行為（嘗試從 list widget 取文本）
        try:
            cur_item = self.lst.currentItem()
            if not cur_item:
                return
            text = cur_item.text()
            evt_id = text.split(":", 1)[0]
            self.remove_requested.emit(self.current_date, evt_id)
        except Exception:
            return



