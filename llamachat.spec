# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['llamachat/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.env', '.'),
        ('llamachat/database/', 'llamachat/database/'),
        ('llamachat/config.py', 'llamachat/'),
        ('llamachat/ui/', 'llamachat/ui/'),
        ('llamachat/utils/', 'llamachat/utils/'),
    ],
    hiddenimports=[
        'backoff',
        'markdown',
        'ollama',
        'dotenv',
        'qasync',
        'sqlmodel',
    ],
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
    [],
    exclude_binaries=True,
    name='llamachat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
)

app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    name='llamachat.app',
    icon='llamachat.icns',
    bundle_identifier='com.fermellone.llamachat',
    info_plist={
        'LSMinimumSystemVersion': '10.12.0',
        'NSHighResolutionCapable': 'True',
        'CFBundleDocumentTypes': [],
        'CFBundleTypeExtensions': [],
        'NSRequiresAquaSystemAppearance': 'No',
    },
    codesign_identity=None,
    entitlements_file=None
)
