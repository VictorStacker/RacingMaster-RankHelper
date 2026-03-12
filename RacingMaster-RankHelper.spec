# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

# 导入版本号
from rm_rank.config import APP_VERSION

datas = [('rm_rank', 'rm_rank')]
binaries = []
hiddenimports = ['rm_rank', 'rm_rank.ui', 'rm_rank.models', 'rm_rank.engines', 'rm_rank.repositories', 'rm_rank.crawler', 'rm_rank.io', 'rm_rank.tuning', 'PyQt6', 'playwright', 'sqlalchemy', 'pydantic', 'bs4']
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('playwright')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'RacingMaster-RankHelper-v{APP_VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
