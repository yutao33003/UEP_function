import os
from scheduler_service.scheduler_manager import SchedulerManager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
music_cache_script_path = os.path.join(BASE_DIR, "tasks", "music_cache_task.py")
reminder_expired_task_path = os.path.join(BASE_DIR, "tasks", "reminder_expired_task.py_task.py")

manager = SchedulerManager()

# 註冊系統排程
manager.register_task("MusicCacheTask", schedule="03:00", system=True, script = music_cache_script_path)
manager.register_task("ReminderExpiredTask", schedule="00:00", system=True, script = reminder_expired_task_path)