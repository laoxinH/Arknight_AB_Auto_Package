<div align="center">

# 🎮 Unity 资源编辑器

**一个专业的多游戏 Unity 资源包处理工具**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/laoxinH/Arknight_AB_Auto_Package?style=social)](https://github.com/laoxinH/Arknight_AB_Auto_Package)

[官方网站](https://www.modwu.com/219.html) • [详细介绍](https://www.modwu.com/219.html) • [赞助支持](https://www.modwu.com/219.html)

</div>

## 📖 简介

Unity 资源编辑器是一款功能强大的游戏资源包处理工具，支持多款热门游戏的 Unity AssetBundle 解密、解包、编辑和重新打包。无论是资源提取、MOD 制作还是游戏研究，本工具都能为您提供便捷的解决方案。

**开发者：** [MOD实验室](https://www.modwu.com)

---

## 🎯 支持的游戏

| 游戏名称        | 英文名称       | 支持状态    |
| --------------- | -------------- | ----------- |
| 🏢 明日方舟     | Arknights      | ✅ 完全支持 |
| ⚔️ 交错战线   | Cross Core     | ✅ 完全支持 |
| 🔄 重返未来1999 | Reverse: 1999  | ✅ 完全支持 |
| 📦 通用资源包   | Standard Unity | ✅ 完全支持 |

> 工具会自动识别游戏类型并选择对应的解密方案，无需手动配置。

---

## ✨ 功能特点

### 核心功能

- 🔓 **智能解密** - 自动识别并解密多种游戏加密格式
- 📦 **资源解包** - 提取 Unity AssetBundle 中的所有资源
- 🔨 **资源打包** - 将修改后的资源重新打包为 AB 文件
- 🖼️ **资源预览** - 实时预览图片、JSON 等资源内容
- 📝 **批量处理** - 支持批量解包/打包操作

### 高级功能

- 🎨 **资源编辑** - 内置资源编辑器，直接修改文本、JSON 配置
- 🧪 **实验室模式** - 快速导出游戏 MOD 所需的资源结构
- 📊 **文件分析** - 显示资源包详细信息和文件结构
- 🎯 **选择性提取** - 通过可视化界面选择需要的资源
- 🌓 **主题切换** - 支持亮色/暗色主题

### 用户体验

- 💻 **现代化界面** - 基于 PyQt6 的美观用户界面
- 📈 **实时进度** - 显示处理进度和详细日志
- ⚡ **高效处理** - 多线程处理，提升大文件处理速度
- 🔍 **智能搜索** - 快速查找和筛选资源文件

---

## 📸 界面预览

### 主界面

![主界面](https://cloudflare-imgbed-env.pages.dev/file/1763639657818_image.png)

### 设置页面

![设置页面](https://cloudflare-imgbed-env.pages.dev/file/1763635795910_image.png)

### 资源编辑页面

![资源编辑页面](https://cloudflare-imgbed-env.pages.dev/file/upload/1753018805324_image.png)

### 导出实验室MOD页面

![导出实验室MOD页面](https://cloudflare-imgbed-env.pages.dev/file/upload/1753019118191_image.png)

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows / macOS / Linux

### 安装步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/laoxinH/Arknight_AB_Auto_Package.git
   cd Arknight_AB_Auto_Package
   ```
2. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```
3. **运行程序**

   ```bash
   python src/main.py
   ```

---

## 📚 使用指南

### 解包资源

1. 点击 **"选择资源包"** 按钮，选择 `.ab` 文件
2. 点击 **"扫描资源包"** 按钮分析文件内容
3. 在文件选择对话框中勾选需要提取的资源（支持预览）
4. 设置输出目录（可选）
5. 点击 **"开始解包"** 按钮开始提取

### 打包资源

1. 点击 **"选择文件夹"** 按钮，选择包含修改后资源的文件夹
2. 配置打包参数（压缩方式、版本等）
3. 点击 **"开始打包"** 按钮生成新的 AB 文件

### 批量处理

1. 进入 **"批量处理"** 标签页
2. 添加多个 AB 文件到处理列表
3. 配置统一的处理参数
4. 点击 **"开始批量处理"** 执行

### 导出实验室 MOD

1. 进入 **"实验室"** 标签页
2. 选择目标游戏和 MOD 类型
3. 配置 MOD 参数
4. 点击 **"导出 MOD"** 生成标准 MOD 结构

---

## 🛠️ 技术架构

```
Arknight_AB_Auto_Package/
├── src/
│   ├── main.py                  # 程序入口
│   ├── config/                  # 配置管理
│   │   ├── config_manager.py
│   │   └── settings.py
│   ├── core/                    # 核心功能
│   │   ├── asset_extractor.py   # 资源提取器
│   │   ├── ab_processor.py      # AB 文件处理器
│   │   └── abprocessor/         # 处理器实现
│   │       ├── BundleProcessor.py
│   │       ├── BundleProcessorManager.py
│   │       └── impl/            # 各游戏实现
│   │           ├── CommonBundleProcessor.py
│   │           ├── CrossCoreBundleProcessor.py
│   │           └── Re1999BundleProcessor.py
│   ├── ui/                      # 用户界面
│   │   ├── main_window.py       # 主窗口
│   │   ├── file_selector.py     # 文件选择器
│   │   ├── settings_dialog.py   # 设置对话框
│   │   └── widgets/             # 自定义组件
│   ├── utils/                   # 工具函数
│   │   ├── logger.py            # 日志系统
│   │   └── BundleValidator.py   # 文件验证
│   └── worker/                  # 异步工作线程
│       ├── asset_worker.py
│       └── batch_asset_worker.py
├── resource/                    # 资源文件
├── requirements.txt             # 依赖列表
└── README.md                    # 说明文档
```

---

## 📦 依赖项

```
UnityPy==1.9.3          # Unity 资源处理核心库
Pillow==10.2.0          # 图片处理库
PyQt6==6.6.1            # GUI 框架
```

完整依赖列表请查看 [requirements.txt](requirements.txt)

---

## 🤝 贡献指南

欢迎提交问题和拉取请求！

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

---

## 💖 支持项目

如果这个项目对您有帮助，请考虑：

- ⭐ 给项目点个 Star
- 🔗 分享给更多的朋友
- 💰 [赞助支持](https://www.modwu.com/219.html)

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 📞 联系我们

- 🌐 官方网站：[https://www.modwu.com/219.html](https://www.modwu.com/219.html)
- 📧 开发者：MOD实验室

---

<div align="center">

**Made with ❤️ by MOD实验室**

[返回顶部](#-unity-资源编辑器)

</div>
