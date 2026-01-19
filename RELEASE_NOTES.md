# 发布说明

## 打包模式变更

### 从单文件模式改为目录模式

**优势：**
- ⚡ **启动速度提升 2-5 倍**：无需解压临时文件
- 📦 **主程序体积更小**：EXE 仅 ~8MB，依赖分离到 `_internal` 目录
- 🐛 **依赖问题更少**：DLL 和 .pyd 文件可直接访问
- 🔍 **易于调试**：可直接查看打包的文件结构
- 🔄 **支持热更新**：可单独替换依赖库

### 文件结构

```
Arknight_AB_Tool/
├── Arknight_AB_Auto_Package.exe  (主程序，~8MB)
└── _internal/                     (依赖库和资源)
    ├── *.dll                      (动态链接库)
    ├── *.pyd                      (Python 扩展模块)
    └── src/resource/              (资源文件)
```

### 用户数据目录

所有用户数据统一管理在：`%LOCALAPPDATA%\ArknightABTool\`

```
%LOCALAPPDATA%\ArknightABTool\
├── logs/           (日志文件)
├── config.json     (配置文件)
└── temp/           (临时文件)
```

**Windows 路径示例：**
`C:\Users\你的用户名\AppData\Local\ArknightABTool\`

## 新功能

### 日志管理
- 查看最新日志
- 打开日志目录
- 清理所有日志
- 日志自动轮转

### 路径管理
- 统一的路径管理系统
- 开发环境和打包环境自动适配
- 支持跨平台（Windows/Linux/macOS）

## 发布流程

### 1. 本地测试打包

```powershell
# 清理旧文件
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# 打包
pyinstaller arknight_AB_Auto_Package.spec --noconfirm

# 测试
.\dist\Arknight_AB_Auto_Package\Arknight_AB_Auto_Package.exe
```

### 2. 创建发布标签

```bash
# 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签（触发 GitHub Actions）
git push origin v1.0.0
```

### 3. GitHub Actions 自动构建

- 自动安装依赖
- 自动打包
- 自动创建 Release
- 自动上传 ZIP 文件

## 用户使用说明

### 系统要求
- Windows 10/11 64位
- 无需安装 Python
- 无需安装其他依赖

### 安装步骤
1. 下载 `Arknight_AB_Tool_vX.X.X_Windows.zip`
2. 解压到任意目录
3. 运行 `Arknight_AB_Auto_Package.exe`

### 注意事项
- ⚠️ 首次运行可能需要等待几秒加载
- ⚠️ 不要删除 `_internal` 目录
- ⚠️ Windows Defender 可能会扫描，请耐心等待
- ✅ 支持便携式使用，可放在 U 盘
- ✅ 卸载只需删除程序目录和用户数据目录

## 开发者说明

### 依赖更新
如果更新了依赖库，需要：
1. 更新 `requirements.txt`
2. 测试打包是否正常
3. 检查是否需要更新 `.spec` 文件

### 新增资源文件
如果添加了新的资源文件：
1. 更新 `arknight_AB_Auto_Package.spec` 中的 `datas`
2. 使用 `path_helper.get_resource_path()` 获取路径

### 调试技巧
```python
# 打印路径信息
from src.utils.path_helper import *

print(f"应用根目录: {get_app_root()}")
print(f"用户数据目录: {get_user_data_dir()}")
print(f"配置目录: {get_config_dir()}")
print(f"日志目录: {get_logs_dir()}")
```

## 常见问题

### Q: 为什么改用目录模式？
A: 单文件模式每次启动都要解压到临时目录，速度慢且容易出现依赖问题。目录模式更稳定、更快速。

### Q: 如何分发给用户？
A: 将整个 `Arknight_AB_Auto_Package` 文件夹打包成 ZIP，用户解压后即可使用。

### Q: 可以改回单文件模式吗？
A: 可以，但不推荐。如需单文件，修改 `.spec` 文件，移除 `exclude_binaries=True` 和 `COLLECT` 部分。

### Q: 打包后文件很大怎么办？
A: 可以使用 UPX 压缩，在 `.spec` 中设置 `upx=True`，但可能触发杀毒软件。

## 版本历史

### v1.0.0 (2026-01-20)
- ✨ 改用目录模式打包
- ✨ 添加统一路径管理
- ✨ 添加日志管理功能
- ✨ 优化启动速度
- 🐛 修复 NumPy C 扩展导入问题
- 🐛 修复 backports.zstd 依赖问题
