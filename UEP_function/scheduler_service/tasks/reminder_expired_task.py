from set_reminder.json_repository.record_controller import TaskController

if __name__ == "__main__":
    reminder = TaskController
    reminder.move_expired_reminders()