"""
使用 PyInstaller 打包 Windows 可执行文件

使用方法:
1. 安装 PyInstaller: pip install pyinstaller
2. 运行此脚本: python build_exe.py
"""
import PyInstaller.__main__
import sys
from pathlib import Path

def build():
    """构建可执行文件"""
    
    # PyInstaller 参数
    args = [
        'run_gui.py',  # 入口文件
        '--name=RacingMaster-RankHelper',  # 可执行文件名
        '--windowed',  # 不显示控制台窗口
        '--onefile',  # 打包成单个文件
        '--icon=icon.ico',  # 应用图标
        '--add-data=rm_rank;rm_rank',  # 包含 rm_rank 包
        '--hidden-import=rm_rank',
        '--hidden-import=rm_rank.ui',
        '--hidden-import=rm_rank.models',
        '--hidden-import=rm_rank.engines',
        '--hidden-import=rm_rank.repositories',
        '--hidden-import=rm_rank.crawler',
        '--hidden-import=rm_rank.io',
        '--hidden-import=PyQt6',
        '--hidden-import=playwright',
        '--hidden-import=sqlalchemy',
        '--hidden-import=pydantic',
        '--collect-all=PyQt6',
        '--collect-all=playwright',
        '--noconfirm',  # 覆盖已存在的文件
    ]
    
    print("开始打包...")
    print(f"参数: {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✓ 打包完成！")
        print(f"可执行文件位置: dist/RacingMaster-RankHelper.exe")
    except Exception as e:
        print(f"\n✗ 打包失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build()
