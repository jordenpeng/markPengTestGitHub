#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_logs.py - 創建logs目錄
"""
import os
from pathlib import Path

# 創建logs目錄
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
print(f"✓ 已創建目錄: {log_dir.absolute()}")
