# -*- mode: python ; coding: utf-8 -*-
import os
import glob
import UnityPy
import archspec
import backports.zstd
import numpy
from PyInstaller.utils.hooks import collect_submodules, collect_all, copy_metadata, collect_dynamic_libs

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

# 自动收集 src 下所有子模块
src_hiddenimports = collect_submodules('src')

# 收集 py7zr 相关依赖
py7zr_datas, py7zr_binaries, py7zr_hiddenimports = collect_all('py7zr')

# 收集 backports.zstd 相关依赖（命名空间包需要特殊处理）
backports_zstd_datas, backports_zstd_binaries, backports_zstd_hiddenimports = collect_all('backports.zstd')

# 收集 backports.zstd 的动态链接库（主要是 _zstd.*.pyd）
backports_zstd_binaries += collect_dynamic_libs('backports.zstd')

# 收集 backports.zstd 的元数据
backports_zstd_datas += copy_metadata('backports.zstd', recursive=True)

# 确保 C 扩展模块被包含（_zstd.*.pyd 或 .so）
backports_zstd_path = os.path.dirname(backports.zstd.__file__)
zstd_ext_files = glob.glob(os.path.join(backports_zstd_path, '_zstd.*.pyd'))
zstd_ext_files += glob.glob(os.path.join(backports_zstd_path, '_zstd.*.so'))
for f in zstd_ext_files:
    backports_zstd_binaries.append((f, 'backports/zstd'))

# 收集 NumPy 相关依赖（解决 C 扩展导入失败问题）
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')

# 手动添加 NumPy 的 .libs 目录（包含所有 DLL 依赖）
numpy_path = os.path.dirname(numpy.__file__)
numpy_libs_path = os.path.join(numpy_path, '.libs')
if os.path.exists(numpy_libs_path):
    for lib_file in glob.glob(os.path.join(numpy_libs_path, '*.dll')):
        numpy_binaries.append((lib_file, 'numpy/.libs'))

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=py7zr_binaries + backports_zstd_binaries + numpy_binaries,
    datas=[
        ('src/resource/icon.webp', 'src/resource'),
        (unitypy_resources, 'UnityPy/resources'),
        (archspec_path, 'archspec'),
        (payme_path, 'src/resource/payme'),  # 添加支付码图片目录
        (about_path, 'src/resource/about'),   # 添加关于页面图片目录
    ] + py7zr_datas + backports_zstd_datas + numpy_datas,
    hiddenimports=[
        'UnityPy.resources',
        'archspec',
        'archspec.cpu',
        'archspec.json',
        # py7zr 和相关压缩库
        'py7zr',
        'pyzstd',
        'multivolumefile',
        'pycryptodomex',
        'inflate64',
        'brotli',
        'texttable',
        # backports.zstd（使用 C 扩展）
        'backports',
        'backports.zstd',
        'backports.zstd._zstd',
        'backports.zstd._zstdfile',
        'backports.zstd._shutil',
        'backports.zstd._streams',
        # NumPy C 扩展
        'numpy',
        'numpy.core',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'numpy.linalg',
        'numpy.linalg.lapack_lite',
        'numpy.linalg._umath_linalg',
        'numpy.fft',
        'numpy.random',
        'numpy.random._common',
        'numpy.random._bounded_integers',
        'numpy.random._mt19937',
        'numpy.random._philox',
        'numpy.random._pcg64',
        'numpy.random._sfc64',
        'numpy.random._generator',
        'numpy.random.bit_generator',
    ] + src_hiddenimports + py7zr_hiddenimports + backports_zstd_hiddenimports + numpy_hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 目录模式打包 - 分离 EXE 和依赖文件
exe = EXE(
    pyz,
    a.scripts,
    [],  # 不打包 binaries
    exclude_binaries=True,  # 关键：不将依赖打包到 exe 中
    name='Arknight_AB_Auto_Package',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='file_version_info.txt',
    icon='src/resource/icon.webp',
    uac_admin=False,
)

# COLLECT 生成目录结构
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Arknight_AB_Auto_Package',  # 输出文件夹名称
) 