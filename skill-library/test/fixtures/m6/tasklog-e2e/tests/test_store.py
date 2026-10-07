from datetime import date

import pytest

import tasklog.store as store_module
from tasklog import TaskStore, overdue_tasks


def test_add_and_list_open():
    store = TaskStore()
    store.add("  write report ")
    assert [t.title for t in store.open_tasks()] == ["write report"]


def test_complete_removes_from_open():
    store = TaskStore()
    store.add("a")
    store.complete("a")
    assert store.open_tasks() == []


def test_complete_unknown_raises():
    with pytest.raises(KeyError):
        TaskStore().complete("nope")


def test_due_date_stored_when_supplied_absent_otherwise():
    store = TaskStore()
    with_due = store.add("with due date", due_date=date(2026, 10, 1))
    without_due = store.add("without due date")
    assert with_due.due_date == date(2026, 10, 1)
    assert without_due.due_date is None


def test_open_task_past_due_is_included():
    store = TaskStore()
    store.add("overdue", due_date=date(2026, 10, 1))
    result = overdue_tasks(store, today=date(2026, 10, 5))
    assert [t.title for t in result] == ["overdue"]


def test_undated_and_completed_tasks_are_excluded():
    store = TaskStore()
    store.add("no due date")
    store.add("completed", due_date=date(2026, 9, 1))
    store.complete("completed")
    result = overdue_tasks(store, today=date(2026, 10, 5))
    assert result == []


def test_today_and_future_due_dates_are_excluded():
    store = TaskStore()
    store.add("due today", due_date=date(2026, 10, 5))
    store.add("due tomorrow", due_date=date(2026, 10, 6))
    result = overdue_tasks(store, today=date(2026, 10, 5))
    assert result == []


def test_ordering_earliest_due_date_first_title_breaks_ties():
    store = TaskStore()
    store.add("Beta", due_date=date(2026, 9, 10))
    store.add("Alpha", due_date=date(2026, 9, 10))
    store.add("Gamma", due_date=date(2026, 9, 1))
    result = overdue_tasks(store, today=date(2026, 10, 5))
    assert [t.title for t in result] == ["Gamma", "Alpha", "Beta"]


def test_injected_reference_date_governs_overdue_status():
    store = TaskStore()
    store.add("task", due_date=date(2026, 10, 10))
    assert overdue_tasks(store, today=date(2026, 10, 5)) == []
    result = overdue_tasks(store, today=date(2026, 10, 15))
    assert [t.title for t in result] == ["task"]


def test_default_reference_date_is_system_date(monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return date(2026, 10, 5)

    monkeypatch.setattr(store_module, "date", FixedDate)

    store = TaskStore()
    store.add("before", due_date=date(2026, 10, 4))
    store.add("after", due_date=date(2026, 10, 6))
    result = overdue_tasks(store)
    assert [t.title for t in result] == ["before"]


def test_due_date_exactly_one_day_before_reference_is_included():
    store = TaskStore()
    store.add("yesterday", due_date=date(2026, 10, 4))
    result = overdue_tasks(store, today=date(2026, 10, 5))
    assert [t.title for t in result] == ["yesterday"]


def test_empty_store_returns_empty_list():
    store = TaskStore()
    assert overdue_tasks(store, today=date(2026, 10, 5)) == []
