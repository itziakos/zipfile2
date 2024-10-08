from pathlib import Path
from setuptools import setup

HERE = Path(__file__).parent
version = (HERE / 'VERSION').read_text().strip()
filename = (HERE / 'zipfile2' / '_version.py')
filename.write_text(f"__version__ = '{version}'\n")

setup()
