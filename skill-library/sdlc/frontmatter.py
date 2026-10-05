"""YAML front matter splitting and parsing."""

from __future__ import annotations

import datetime

import yaml


def split(text: str) -> tuple[str | None, int]:
    """Return (raw front matter or None, 0-based index of first body line)."""
    lines = text.split("\n")
    if not lines or lines[0].lstrip("﻿").strip() != "---":
        return None, 0
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[1:i]), i + 1
    return None, 0


def parse(raw: str) -> dict:
    """Parse YAML into a mapping; dates are normalised to ISO strings. Raises ValueError."""
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        first = str(exc).strip().splitlines()[0] if str(exc).strip() else "invalid YAML"
        raise ValueError(f"invalid YAML: {first}") from exc
    except ValueError as exc:  # e.g. an unquoted date with an impossible month/day
        raise ValueError(f"invalid YAML value: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("front matter must be a YAML mapping")
    return {str(k): _normalise(v) for k, v in data.items()}


def _normalise(value):
    if type(value) is datetime.date:
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    return value


def dump(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)
