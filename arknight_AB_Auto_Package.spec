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

# 获取项目资源目录
resource_path = os.path.join('src', 'resource')
payme_path = os.path.join(resource_path, 'payme')
about_path = os.path.join(resource_path, 'about')

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
        (payme_path, 'src/resource/payme'),  # 添加支付码图片目录
        (about_path, 'src/resource/about'),   # 添加关于页面图片目录
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
    name='Arknight_AB_Auto_Package',
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
    version='file_version_info.txt',  # 添加版本信息文件
    icon='src/resource/icon.webp',  # 添加图标
    uac_admin=False,  # 不需要管理员权限
    # 添加文件信息
    file_description='Unity AB Package Tool',
    product_name='Unity AB Package Tool',
    legal_copyright='Copyright (c) 2025',
    company_name='MOD 实验室',
    # 优化选项
    optimize=2,  # 使用优化
) 