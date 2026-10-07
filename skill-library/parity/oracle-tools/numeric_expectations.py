#!/usr/bin/env python3
"""Generate parity/numeric-expectations.json from the PYTHON ORACLE: `.2f`/`.3f` formatting, round(x, 3) and the
find-overlaps score formula (sdlc/query.py). A frozen M7 asset; the Node numerics must reproduce it exactly."""

import json
import random
from fractions import Fraction
from pathlib import Path

LIB = Path(__file__).resolve().parents[2]
WEIGHTS = {"title": 0.5, "purpose": 0.3, "refs": 0.2}  # sdlc/query.py


def fmt(x: float) -> dict:
    return {"x": repr(x), "f2": f"{x:.2f}", "f3": f"{x:.3f}", "r3": repr(round(x, 3))}


def score(t: float, p: float, r: float, sp: bool, sr: bool) -> float:
    signals = {"title": True, "purpose": sp, "refs": sr}
    total = sum(w for k, w in WEIGHTS.items() if signals[k])
    return (t * WEIGHTS["title"] + p * WEIGHTS["purpose"] * sp + r * WEIGHTS["refs"] * sr) / total


TOKEN_INPUTS = [
    "", "of the", "Docs and Uses", "bus gas bass class glass", "yes this is it", "plans plan plant plants", "ABC abc", "Reports, REPORTS; report.", "alpha-bravo_charlie delta9 99s 100s",
    "caf\u00e9 na\u00efve", "\u65e5\u672c\u8a9e test", "a an the of for and to in on with or", "uses", "use", "does", "its", "status", "this", "news", "lens", "jazz", "kiss", "loss",
    "series", "species", "access", "addresses", "bonus", "analysis", "dates", "files", "tools", "pass", "mass", "boss", "oss", "ss", "sss", "ssss", "s", "ab", "abs", "abcs", "abcds",
]


def main() -> None:
    import sys
    sys.path.insert(0, str(LIB))
    from sdlc.query import tokens
    rng = random.Random(20261005)
    xs = set()
    for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 25, 32, 40, 48, 50, 64, 80, 100, 125, 128, 160, 200, 250, 256, 400, 500, 512, 1000, 2000, 4000, 8000):
        xs.update(k / n for k in range(0, n + 1))
    xs.update(rng.random() for _ in range(6000))
    xs.update(round(rng.random(), rng.choice((2, 3, 4))) for _ in range(2000))
    fractions = [Fraction(a, b) for b in range(1, 13) for a in range(0, b + 1)]
    fr = sorted({float(f) for f in fractions})
    cases = []
    for _ in range(4000):
        t, p, r = rng.choice(fr), rng.choice(fr), rng.choice(fr)
        sp, sr = rng.random() < 0.6, rng.random() < 0.6
        s = score(t, p, r, sp, sr)
        cases.append({"title": repr(t), "purpose": repr(p), "refs": repr(r), "sp": sp, "sr": sr, "score": repr(s), "r3": repr(round(s, 3)), "f2_of_r3": f"{round(s, 3):.2f}"})
    out = {"source": "python-1.0.0rc1", "format": [fmt(x) for x in sorted(xs)], "score": cases,
           "tokens": [{"text": t, "tokens": sorted(tokens(t))} for t in TOKEN_INPUTS]}
    (LIB / "parity" / "numeric-expectations.json").write_text(json.dumps(out) + "\n")
    ties = sum(1 for x in sorted(xs) if f"{x:.2f}" != f"{x + 0:.2f}" or True)
    print(f"{len(out['format'])} format cases, {len(cases)} score cases")


if __name__ == "__main__":
    main()
