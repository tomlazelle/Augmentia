"""Build hook: copy the canonical `skills/` and `shared/` trees into the package as `sdlc/library/`.

The sources stay where they are (one canonical copy, never forked); only the built distribution carries them
so an installed `sdlc` can locate Skills and shared conventions without a source checkout.
"""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).resolve().parent


class BuildPy(build_py):
    def run(self):
        super().run()
        if self.dry_run:
            return
        target = Path(self.build_lib) / "sdlc" / "library"
        for name in ("skills", "shared"):
            dest = target / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(ROOT / name, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


setup(cmdclass={"build_py": BuildPy})
