# calendar_controller.py
class CalendarController:
    def __init__(self, model, widget, event_adapter, event_list_widget):
        self.model = model
        self.widget = widget
        self.adapter = event_adapter
        self.event_list = event_list_widget

        # connect signals
        self.widget.date_selected.connect(self.on_date_selected)
        self.widget.month_changed.connect(self.on_month_changed)
        self.event_list.add_requested.connect(self.on_add_requested)
        self.event_list.remove_requested.connect(self.on_remove_requested)

    def on_date_selected(self, iso_date):
        # 2. 告訴 event_list 顯示
        self.event_list.show_events(iso_date)
        # 3. 記錄選取的日期（model）
        self.model.selected_date_iso = iso_date

    def on_month_changed(self, y, m):
        # 需要時做額外動作（例如 lazy load events）
        pass

    def on_add_requested(self, iso_date):
       pass

    def on_remove_requested(self, iso_date, event_id):
        self.adapter.remove_event(iso_date, event_id)
        self.on_date_selected(iso_date)
