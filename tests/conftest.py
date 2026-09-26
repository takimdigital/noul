#!/usr/bin/env python3
"""conftest.py — ensure noul is importable in tests."""
import sys
import os

# Add parent of noul/ to sys.path (two levels up from tests/)
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, repo_root)
