#!/bin/bash
if command -v python3 &>/dev/null; then
  python3 start_app.py
elif command -v python &>/dev/null; then
  python start_app.py
else
  echo "Error: Python is not installed or not in PATH."
  exit 1
fi
