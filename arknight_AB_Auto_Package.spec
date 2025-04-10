# -*- mode: python ; coding: utf-8 -*-
import os
import UnityPy
import archspec

block_cipher = None

# 获取 UnityPy 资源目录
unitypy_path = os.path.dirname(UnityPy.__file__)
unitypy_resources = os.path.join(unitypy_path, 'resources')
unitypy_fmod = os.path.join(unitypy_path, 'lib/FMOD/Windows/x64')

# 获取 archspec 资源目录
archspec_path = os.path.dirname(archspec.__file__)

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        (os.path.join(unitypy_fmod, 'fmod.dll'), 'UnityPy/lib/FMOD/Windows/x64'),
    ],
    datas=[
        ('src/resource/icon.webp', 'src/resource'),
        (unitypy_resources, 'UnityPy/resources'),
        (archspec_path, 'archspec'),
    ],
    hiddenimports=[
        'UnityPy.resources',
        'archspec',
        'archspec.cpu',
        'archspec.json',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='明日方舟资源包处理工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 临时设置为 True 以查看错误信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/resource/icon.webp'
) 