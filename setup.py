import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.editable_wheel import editable_wheel

ROOT_DIR = Path(__file__).parent
BUILD_SCRIPT = ROOT_DIR / "scripts" / "build_gkeyll.sh"


def _build_gkeyll():
    subprocess.run(["sh", str(BUILD_SCRIPT)], check=True, cwd=ROOT_DIR)


class BuildPyWithGkeyll(build_py):
    def run(self):
        _build_gkeyll()
        super().run()


class DevelopWithGkeyll(develop):
    def run(self):
        _build_gkeyll()
        super().run()


class EditableWheelWithGkeyll(editable_wheel):
    def run(self):
        _build_gkeyll()
        super().run()


setup(
    cmdclass={
        "build_py": BuildPyWithGkeyll,
        "develop": DevelopWithGkeyll,
        "editable_wheel": EditableWheelWithGkeyll,
    },
)
