# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_gui.py'],
    pathex=['.', 'src'],
    binaries=[],
    datas=[
        # Bundle templates and definitions from source to root of dist
        ('src/lcr/core/container/templates', 'templates'),
        ('src/lcr/core/container/definitions', 'definitions'),
        # Bundle LICENSE file
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'jinja2',
        'docker',
        'chardet',
        'PySide6.QtXml',
        'lcr.utils.path_helper',
        'lcr.core.container.generator',
        'lcr.core.container.manager',
        'lcr.core.container.worker',
        'lcr.core.history.manager',
        'lcr.core.detector.analyzer',
    ],
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
    [],
    exclude_binaries=True,
    name='LCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LCR',
)
