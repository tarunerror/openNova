# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for openNova desktop application.
Build with: pyinstaller openNova.spec
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include config files
        ('.env', '.'),
        # Include any model files if needed
        # ('models', 'models'),
    ],
    hiddenimports=[
        # Core imports
        'multiprocessing',
        'queue',

        # GUI
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',

        # LLM
        'litellm',
        'openai',
        'anthropic',

        # Audio
        'faster_whisper',
        'edge_tts',
        'pyaudio',
        'openwakeword',

        # Vision & Control
        'pyautogui',
        'mss',
        'pywinauto',
        'PIL',

        # Memory
        'chromadb',
        'chromadb.config',

        # Scheduler & Watcher
        'apscheduler',
        'apscheduler.schedulers.background',
        'watchdog',
        'watchdog.observers',

        # System
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'win32api',
        'win32con',
        'win32gui',

        # Utilities
        'dotenv',
        'requests',

        # Application modules
        'src.core',
        'src.gui',
        'src.audio',
        'src.llm',
        'src.memory',
        'src.vision',
        'src.actions',
        'src.plugins',
        'src.scheduler',
        'src.watcher',
        'src.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.distutils',
        'tkinter',
    ],
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
    name='openNova',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one
    uac_admin=True,  # Request admin privileges
)
