# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller main_window.spec
# (этот файл дублирует main_window.spec для совместимости)

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('main_icon.ico', '.'),
]
datas += collect_data_files('tkcalendar')
datas += collect_data_files('babel')

hiddenimports = collect_submodules('db')
hiddenimports += collect_submodules('resources')
hiddenimports += [
    'openpyxl',
    'fpdf',
    'PIL',
    'babel',
    'tkcalendar',
]

a = Analysis(
    ['main_window.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Магазин',
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
    icon='main_icon.ico',
)
