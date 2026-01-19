# PyInstaller hook for backports.zstd
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, copy_metadata
import os
import glob

# backports.zstd 使用 C 扩展（_zstd.*.pyd），不是 CFFI
# 只导入实际存在的模块
hiddenimports = [
    'backports.zstd._zstd',
    'backports.zstd._zstdfile',
    'backports.zstd._shutil',
    'backports.zstd._streams',
]

# 收集数据文件和元数据
datas = collect_data_files('backports.zstd')
datas += copy_metadata('backports.zstd', recursive=True)

# 收集动态链接库（主要是 _zstd.*.pyd 或 .so）
binaries = collect_dynamic_libs('backports.zstd')

# 手动确保 C 扩展模块被包含
try:
    import backports.zstd
    backports_zstd_path = os.path.dirname(backports.zstd.__file__)
    
    # 查找 _zstd C 扩展文件
    ext_patterns = [
        '_zstd.*.pyd',   # Windows
        '_zstd.*.so',    # Linux
    ]
    
    for pattern in ext_patterns:
        ext_files = glob.glob(os.path.join(backports_zstd_path, pattern))
        for f in ext_files:
            binaries.append((f, 'backports/zstd'))
            
except Exception as e:
    print(f"Warning: Failed to collect backports.zstd binaries: {e}")
