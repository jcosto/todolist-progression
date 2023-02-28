from dataclasses import dataclass, asdict

TASK_ONGOING = 1
TASK_COMPLETED = 2
TASK_DELETED = 3

@dataclass
class Task():
    """
    states: TASK_ONGOING, TASK_COMPLETED, TASK_DELETED
    """
    name: str
    state: int
    id: int

    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}


