# -*- mode: python ; coding: utf-8 -*-
# Auto-generated spec file for OZONScrappy

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (r'C:\\Users\\nurja\\OneDrive\\Рабочий стол\\ozon_seller_scrappy\\venv\\Lib\\site-packages\\selenium_stealth\\js', 'selenium_stealth/js'),
    ],
    hiddenimports=['selenium_stealth', 'selenium', 'undetected_chromedriver'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OZONScrappy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консоли - красивый GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
)
