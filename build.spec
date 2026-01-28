# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DB Agent
Creates a standalone executable for Windows
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the project root directory
project_root = os.path.dirname(os.path.abspath(SPEC))

# Collect data files for rich (includes unicode data)
rich_datas = collect_data_files('rich')

# Collect all submodules for packages that have dynamic imports
rich_hiddenimports = collect_submodules('rich')

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Include config directory
        ('config', 'config'),
    ] + rich_datas,
    hiddenimports=[
        # Database drivers
        'pg8000',
        'pymysql',
        # LLM clients
        'openai',
        'anthropic',
        'google.generativeai',
        # Web framework (for API mode)
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # Pydantic
        'pydantic',
        'pydantic_core',
        # Prompt toolkit
        'prompt_toolkit',
        # Other
        'multipart',
        'python_multipart',
    ] + rich_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'test',
        'tests',
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
    [],
    exclude_binaries=True,
    name='db-agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='db-agent',
)
