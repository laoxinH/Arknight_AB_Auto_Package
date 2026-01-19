# 配置系统说明

## 概述

配置系统提供了应用程序设置的持久化存储功能，确保用户的偏好设置在重启应用后依然保留。

## 目录结构

```
src/config/
├── __init__.py           # 模块初始化
├── config_manager.py     # 配置管理器（单例模式）
└── settings.py           # 配置数据模型
```

## 配置文件位置

配置文件会自动保存在系统用户目录下，确保在开发环境和打包环境都能正常工作：

- **Windows**: `%LOCALAPPDATA%\ArknightABTool\config.json`
  - 例如: `C:\Users\用户名\AppData\Local\ArknightABTool\config.json`

- **Linux/Mac**: `~/.config/ArknightABTool/config.json`
  - 例如: `/home/用户名/.config/ArknightABTool/config.json`

## 当前支持的配置项

### 主题设置
- `theme_mode`: 主题模式 (auto/light/dark)
  - `auto`: 自动跟随系统主题
  - `light`: 强制浅色主题
  - `dark`: 强制深色主题

### 窗口设置
- `window_width`: 窗口宽度
- `window_height`: 窗口高度
- `window_x`: 窗口X位置
- `window_y`: 窗口Y位置
- `window_maximized`: 是否最大化

### 路径设置
- `last_output_dir`: 上次使用的输出目录
- `last_input_dir`: 上次使用的输入目录

### 其他设置（预留扩展）
- `auto_check_update`: 是否自动检查更新
- `language`: 界面语言
- `log_level`: 日志级别

## 使用方法

### 基本使用

```python
from src.config.config_manager import ConfigManager

# 获取配置管理器实例（单例）
config = ConfigManager()

# 获取配置项
theme = config.get('theme_mode')
last_dir = config.get('last_input_dir', '/default/path')

# 设置配置项（立即保存）
config.set('theme_mode', 'dark')

# 批量更新配置
config.update(
    theme_mode='dark',
    window_width=1200,
    save_immediately=True
)

# 获取配置文件路径
config_path = config.get_config_path()

# 重置为默认配置
config.reset()
```

### 在UI组件中使用

```python
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        
        # 恢复窗口大小
        width = self.config.get('window_width', 800)
        height = self.config.get('window_height', 600)
        self.resize(width, height)
    
    def closeEvent(self, event):
        # 保存窗口大小
        self.config.update(
            window_width=self.width(),
            window_height=self.height()
        )
        event.accept()
```

## 扩展配置项

如需添加新的配置项，只需修改 `settings.py` 中的 `AppSettings` 类：

```python
@dataclass
class AppSettings:
    # 现有配置项...
    
    # 新增配置项
    new_setting: str = "default_value"
    another_setting: bool = True
```

新增的配置项会自动支持读取、保存和持久化。

## 配置导入/导出

```python
# 导出配置
config.export_config('/path/to/backup.json')

# 导入配置
config.import_config('/path/to/backup.json')
```

## 注意事项

1. **单例模式**: `ConfigManager` 使用单例模式，全局只有一个实例
2. **自动保存**: 默认情况下修改配置会立即保存，可通过 `save_immediately=False` 参数延迟保存
3. **线程安全**: 当前实现不是线程安全的，如需在多线程环境使用需要添加锁机制
4. **配置迁移**: 当 `AppSettings` 结构变化时，旧配置文件中不存在的字段会使用默认值
5. **打包环境**: 配置文件保存在用户目录，确保打包后也能正常读写

## 配置文件示例

```json
{
    "theme_mode": "dark",
    "window_width": 1200,
    "window_height": 800,
    "window_x": 100,
    "window_y": 100,
    "window_maximized": false,
    "last_output_dir": "C:\\Users\\User\\Desktop",
    "last_input_dir": "C:\\Users\\User\\Documents",
    "auto_check_update": true,
    "language": "zh_CN",
    "log_level": "INFO"
}
```
