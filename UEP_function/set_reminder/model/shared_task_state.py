import dataclasses


@dataclasses.dataclass
class SharedTaskState:
    id: str
    title: str = ""
    type: str = "work"
    start_time: str = ""
    end_time: str = ""
    description: str = ""
    priority: str = "medium"
    alert1: str = "None"
    alert2: str = "None"
    repeat: bool = False
    finish: bool = False
    is_new_task: bool = False