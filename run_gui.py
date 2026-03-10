#!/usr/bin/env python3
"""启动图形界面"""
import sys
sys.argv.append("--gui")

from rm_rank.main import main

if __name__ == "__main__":
    main()
