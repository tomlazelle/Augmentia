"""A tiny in-memory task list."""

from dataclasses import dataclass
from datetime import date


@dataclass
class Task:
    title: str
    done: bool = False
    due_date: date | None = None


class TaskStore:
    def __init__(self):
        self._tasks: list[Task] = []

    def add(self, title: str, due_date: date | None = None) -> Task:
        task = Task(title.strip(), due_date=due_date)
        self._tasks.append(task)
        return task

    def complete(self, title: str) -> Task:
        for task in self._tasks:
            if task.title == title and not task.done:
                task.done = True
                return task
        raise KeyError(title)

    def open_tasks(self) -> list[Task]:
        return [t for t in self._tasks if not t.done]


def overdue_tasks(store: TaskStore, today: date | None = None) -> list[Task]:
    reference_date = today if today is not None else date.today()
    overdue = [
        t
        for t in store.open_tasks()
        if t.due_date is not None and t.due_date < reference_date
    ]
    return sorted(overdue, key=lambda t: (t.due_date, t.title))
