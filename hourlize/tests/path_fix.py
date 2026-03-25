"""
Patch to enable imports of scripts in hourlize by tests.
To use, simply use: ``import pathfix as _`` at the top of
a test script.
"""
from pathlib import Path
import sys

HOURLIZE_PATH = Path(__file__).parent.parent
sys.path.append(HOURLIZE_PATH.as_posix())
