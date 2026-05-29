import os
import sys

# Ensure the backend directory is in the Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main_sqlite import app
