import os
import sys
from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from set_reminder.adapters.event_adapter import EventAdapter
from set_reminder.animate import gradually_enter_ani, slide_stack
from set_reminder.services.task_service import TaskService
from set_reminder.view import sorting_ui, today_list_ui
from set_reminder.calendar import calendar_ui
from set_reminder.json_repository.record_controller import TaskController, TypeController
from set_reminder.view.overlay.edit_overlay import EditTaskOverlay, EditTaskWidget
from set_reminder.view.overlay.simple_overlay import ConfirmDialog
from set_reminder.view.overlay.gray_background_overlay import AddTypeCard, TypeTaskOverlay
from set_reminder.view.overlay.overlay_controller import OverlayController
from set_reminder.view.overlay.overlay_factory import OverlayFactory


class ReminderMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 500)
        self.setWindowTitle("Reminder")
        self.BREAKPOINT_WIDTH = 800

        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._handle_resize_change)

        self._last_is_small = self.width() < self.BREAKPOINT_WIDTH  # 記錄上一次大小狀態
        self.is_overlay = False
        self.is_on_edit = False

        self.task_controller = TaskController()
        self.type_controller = TypeController()
        self.event_adapter = EventAdapter(self.task_controller)
        self.overlay_controller = OverlayController(self)
        self.overlay_factory = OverlayFactory
        self.task_service = TaskService(
            event_adapter=self.event_adapter,
            type_controller=self.type_controller,
        )

        self.overlay_factory.register("task_overlay", TypeTaskOverlay)
        self.overlay_factory.register("edit_overlay", EditTaskOverlay)
        self.overlay_factory.register("confirm_overlay", ConfirmDialog)
        self.overlay_factory.register("type_edit_overlay", AddTypeCard)

        self.stack = QStackedWidget()
        self.sorting_widget = sorting_ui.SortingUI(self.event_adapter, self.overlay_controller, self.type_controller, self.task_service)
        self.today_list_widget = today_list_ui.TodayListUI(self.event_adapter, self.overlay_controller, self.type_controller, self.task_service)
        self.calendar_widget = calendar_ui.CalendarUI(self.event_adapter, self.overlay_controller, self.type_controller, self.task_service)
        self.edit_task_widget = EditTaskWidget(self,type_controller= self.type_controller)
        self.stack.addWidget(self.today_list_widget)
        self.stack.addWidget(self.sorting_widget)
        self.stack.addWidget(self.calendar_widget)
        self.stack.addWidget(self.edit_task_widget)
        self.stack.setCurrentIndex(0)

        self.task_service.show_editor_requested.connect(self.on_show_editor_requested)
        self.edit_task_widget.confirmed_requested.connect(self.on_save_task_request)
        self.edit_task_widget.back_requested.connect(self.on_back_from_edit)

        pixmap_path = os.path.join(os.path.dirname(__file__), "image","background.png")
        self.stack.setStyleSheet(f"""
            QMainWindow {{
                border-image: url({pixmap_path}) 0 0 0 0 stretch stretch;
            }}
        """)
        self.today_list_widget.switch_page.connect(self.switch_page)
        self.sorting_widget.switch_page.connect(self.switch_page)
        self.calendar_widget.switch_page.connect(self.switch_page)

        self.setCentralWidget(self.stack)

    def switch_page(self, index):
        cur = self.stack.currentIndex()
        # 決定方向： index > cur -> 左滑（新頁由右入），否則右滑
        direction = 'left' if index > cur else 'right'
        try:
            slide_stack(self.stack, index, direction=direction)
        except Exception:
            # fallback
            self.stack.setCurrentIndex(index)

    def on_show_editor_requested(self, state, is_overlay = False, parent = None):
        """決策中心 — 保證在切換時只顯示一種 editor，並同步 state 到 overlay/form"""
        is_maximized = self.windowState() == Qt.WindowMaximized
        current_is_small = self.width() < self.BREAKPOINT_WIDTH

        # 保存傳入參數
        self._current_edit_state = state
        self._original_parent = parent
        self.is_overlay = is_overlay

        from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
        from set_reminder.view.overlay.edit_overlay import EditTaskOverlay

        # 若 parent 是 TypeTaskOverlay，視為「嵌入的父層」
        original_parent = parent if isinstance(parent, TypeTaskOverlay) else None

        # helper: 關閉所有 edit_overlay（避免 overlay 與 embedded 同時顯示）
        def _close_all_edit_overlays():
            try:
                for ov in list(self.overlay_controller.active_overlays.values()):
                    if ov is None:
                        continue
                    try:
                        if (hasattr(ov, "objectName") and ov.objectName() == "edit_overlay") or isinstance(ov, EditTaskOverlay):
                            try:
                                ov.close()
                            except Exception:
                                try:
                                    ov.hide()
                                except Exception:
                                    pass
                    except Exception:
                        # 保險性 fallback: 嘗試 hide
                        try:
                            ov.hide()
                        except Exception:
                            pass
            except Exception:
                pass

        # helper: 隱藏 embedded editor（不清掉 _current_edit_state）
        def _hide_embedded_preserve_state():
            try:
                if self.edit_task_widget.isVisible():
                    self.edit_task_widget.hide()
            except Exception:
                pass
            # 如果之前嵌入在 TypeTaskOverlay，恢復 parent content
            embedded_parent = getattr(self, "_embedded_parent", None)
            if embedded_parent:
                try:
                    if hasattr(embedded_parent, "content_area"):
                        embedded_parent.content_area.show()
                except Exception:
                    pass
                self._embedded_parent = None
            self.is_on_edit = False

        # 決策：大畫面（或最大化）且要求嵌入式 → 顯示 embedded
        if (is_maximized or not current_is_small) and not is_overlay:
            # 關閉所有 popup edit_overlay，避免重疊
            _close_all_edit_overlays()

            if original_parent:
                # 嵌入到 TypeTaskOverlay 上（父層保留）
                self._embedded_parent = original_parent
                # 以浮層形式 reparent 並同步 state
                self.edit_task_widget.reparent_to(state = self._current_edit_state, new_parent = original_parent)
                try:
                    if hasattr(original_parent, 'content_area'):
                        original_parent.content_area.hide()
                except Exception:
                    pass
            else:
                # 嵌入到主視窗（或其他容器）
                self._embedded_parent = None
                self.edit_task_widget.form.set_state_and_sync(state = self._current_edit_state, new_parent = self)

            self.is_on_edit = True
            self.previous_page_index = self.stack.currentIndex()
            self.stack.setCurrentWidget(self.edit_task_widget)
            self.edit_task_widget.raise_()
            self.edit_task_widget.show()

        else:
            # 使用 popup overlay（小視窗/行動模式）
            # 先隱藏 embedded（保留 state）
            _hide_embedded_preserve_state     ()

            popup_parent = self if not is_overlay else parent

            overlay = self.overlay_controller.show(
                "edit_overlay",
                parent=self.window(),
                state=self._current_edit_state,
                embedded_con = False,    # popup = active_overlay
                close_previous = False,
                type_controller=self.type_controller
            )

            # 即使 overlay 是重用的，也要強制把最新 state 同步到 overlay.form
            try:
                if overlay and hasattr(overlay, "form"):
                    new_parent_for_form = getattr(overlay, "container", overlay)
                    overlay.form.set_state_and_sync(self._current_edit_state, new_parent=new_parent_for_form)
                    overlay.raise_()
            except Exception:
                pass

            # overlay 的關閉處理
            def overlay_close():
                self.is_on_edit = False
                try:
                    overlay.close()
                except Exception:
                    pass

            self.is_on_edit = True
            if overlay:
                try:
                    overlay.confirmed_requested.connect(self.on_save_task_request)
                    overlay.back_requested.connect(overlay_close)
                except Exception:
                    pass

        # 最後更新上一次的大小標記
        self._last_is_small = current_is_small

    @pyqtSlot() 
    def on_back_from_edit(self):
        self.edit_task_widget.hide()
        self._current_edit_state = None
        self.is_on_edit = False

        # 若嵌入在 overlay，恢復顯示父層內容
        if hasattr(self, "_embedded_parent") and self._embedded_parent:
            parent = self._embedded_parent
            if hasattr(parent, "content_area"):
                parent.content_area.show()
            self._embedded_parent = None


    @pyqtSlot() 
    def on_save_task_request(self):
        """
        處理「儲存」訊號 (來自「嵌入式」或「彈窗式」)
        """
        state_to_save = None
        sender = self.sender() # 找出是誰發的訊號
        
        if sender == self.edit_task_widget:
            # 來自「嵌入式」
            state_to_save = sender.form.state
            # 如果之前是嵌入在 TypeTaskOverlay，恢復其內容顯示
            from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
            embedded_parent = getattr(self, '_embedded_parent', None)
            if isinstance(embedded_parent, TypeTaskOverlay):
                if hasattr(embedded_parent, 'content_area'):
                    embedded_parent.content_area.show()
                self._embedded_parent = None

            self.on_back_from_edit()
            
        elif isinstance(sender, EditTaskOverlay):
            # 來自「彈窗式」
            state_to_save = sender.form.state
            sender.close() # 關閉「彈窗」
            
        if state_to_save:
            self.task_service.save_task(state_to_save)
            sender.form.state.is_new_task = False
            # 刷新所有列表
            self.today_list_widget.refresh_list()

            #self.sorting_widget.refresh_data()
            if self.calendar_widget.current_date:
                self.calendar_widget.on_date_selected(self.calendar_widget.current_date)

            from set_reminder.view.overlay.gray_background_overlay import TypeTaskOverlay
            try:
                for ov in list(self.overlay_controller.active_overlays.values()):
                    if isinstance(ov, TypeTaskOverlay) and getattr(ov, "isVisible", lambda: False)():
                        try:
                            ov.refresh_data()
                        except Exception as e:
                            print(f"[refresh] TypeTaskOverlay.refresh_data() failed: {e}")
            except Exception as e:
                print(f"[refresh_all_type_overlays] error: {e}")


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(300)  # 等待300ms後再執行一次

    def _handle_resize_change(self):
        if not getattr(self, "is_on_edit", False):
            return 
        if not hasattr(self, "_current_edit_state"):
            return

        if getattr(self, "is_overlay", False):
            return 

        is_small = self.width() < self.BREAKPOINT_WIDTH

        if is_small != self._last_is_small:
            print(f"[resize] breakpoint crossed ({'small' if is_small else 'large'})")

            # 更新狀態
            self._last_is_small = is_small

            # 呼叫你的 on_show_editor_requested 重新配置
            # 注意：當 is_small True 時應切換為 overlay（is_overlay=True）
            self.on_show_editor_requested(
                self._current_edit_state,
                is_overlay=False,
                parent=getattr(self, "_embedded_parent", getattr(self, "_original_parent", None))
            )
                

def main():
    # 建立應用程式實例
    app = QApplication(sys.argv)

    # 建立主視窗
    window = ReminderMainWindow()
    window.show()

    # 進入事件迴圈
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()



