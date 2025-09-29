class SchedulerManager:
    def __init__(self):
        self.task = {}

    def register_task(self, name, schedule, func = None, system = False, script = None):
        self.task[name] = {"schedule" :schedule, "func": func, "system" : system, "script": script}
        if system and script:
            self._register_system_task(name, schedule, script)

    def _register_system_task(self, name, schedule, script):
        """註冊系統腳本"""
        import platform, subprocess
        result = subprocess.run(f'schtasks /Query /TN "{name}"', shell=True, capture_output=True, text=True)
        if "ERROR:" in result.stdout:
            cmd = f'schtasks /Create /SC DAILY /TN "{name}" /TR "python {script}" /ST {schedule}'
            subprocess.run(cmd, shell=True)

    def run_all(self):
        for name, task in self.tasks.items():
            if task["func"]:
                print(f"▶️ 執行任務 {name}")
                task["func"]()