# 🎬 Agnes AI 智能创作助手

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.x-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

基于 [Agnes AI](https://agnes-ai.com/) API 和 PyQt5 开发的桌面级 AI 视频生成 GUI 工具，支持：

- 🎥 **AI 视频生成**：通过文字描述生成高质量 AI 视频
- 💬 **AI 智能对话**：与 AI 对话进行创意探讨
- 🎭 **角色档案管理**：创建和管理角色档案，实现角色一致性
- 📖 **漫剧/短剧生成**：自动生成分镜剧本，批量生成场景视频
- 📂 **数据持久化**：配置、项目、视频统一保存，下次打开继续创作

---

## ✨ 功能特性

### 🎥 AI 视频生成
- 支持自定义分辨率（720p / 1080p / 2K / 4K）
- 支持自定义帧数和帧率
- 实时进度显示和状态反馈
- 视频下载保存功能

### 💬 AI 智能对话
- 基于 Agnes AI 大模型的智能对话
- 支持多轮对话上下文
- 可用于剧本创作、创意发散

### 🎭 角色档案管理
- 创建角色档案（姓名、性别、年龄、外貌、服装、性格、背景）
- 角色描述自动拼接，确保视频生成时角色一致性
- 支持项目内多个角色管理

### 📖 漫剧/短剧生成
- AI 自动生成分镜剧本
- 手动编辑场景描述
- 批量生成所有场景视频
- 按项目组织管理创作内容

### 📂 数据持久化
- 可自定义数据保存目录
- 配置自动保存和加载
- 项目数据持久化存储
- 视频下载保存到指定目录

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyQt5
- requests

### 安装

```bash
# 克隆项目
git clone https://github.com/your-username/AgnesAI-Video-Generator.git
cd AgnesAI-Video-Generator

# 安装依赖
pip install PyQt5 requests
```

### 运行

```bash
python main.py
```

### 使用打包版本

从 [Releases](https://github.com/hackerschina/AgnesAI-Video-Generator/releases) 下载最新的 exe 版本，双击即可运行。

---

## 📖 使用说明

### 1. 配置 API Key

1. 首次运行会提示配置 API
2. 输入你的 [Agnes AI](https://agnes-ai.com/) API Key
3. 默认 API Base URL：`https://apihub.agnes-ai.com`
4. 点击"💾 保存配置"保存设置
5. 点击"🔌 测试连接"验证 API 是否正常

### 2. 设置数据目录

1. 点击"📁 选择目录"选择保存位置
2. 所有配置、项目、视频都会保存到此目录
3. 支持新建目录

### 3. 生成视频

1. 切换到"🎬 视频生成"标签页
2. 输入视频描述（提示词）
3. 设置参数：分辨率、帧数、帧率
4. 点击"🎬 生成视频"开始生成
5. 等待生成完成，点击视频链接观看或下载保存

### 4. 角色一致性创作

1. 在项目列表中创建新项目
2. 添加角色档案（姓名、外貌、服装等）
3. 在生成视频时，角色描述会自动包含
4. 确保同一角色在不同场景中保持一致

### 5. 漫剧/短剧生成

1. 创建漫剧项目
2. 在"🖼️ 漫剧生成"标签页输入故事描述
3. 点击"📝 生成分镜剧本"让 AI 自动生成
4. 编辑每个场景的描述
5. 点击"🎬 批量生成所有场景"

---

## 🏗️ 项目结构

```
AgnesAI_Data/                    # 数据保存目录（可自定义）
├── config.json                  # 配置文件
├── projects/                    # 项目文件夹
│   └── {project_id}.json        # 项目数据（角色、场景、视频等）
└── videos/                      # 视频下载文件夹
    └── {video_id}.mp4           # 下载的视频

main.py                          # 主程序
error.log                        # 错误日志
```

---

## 📸 截图

![主界面](screenshots/main_window.png)
*主界面：左侧配置面板 + 右侧功能标签页*

![视频生成](screenshots/video_generation.png)
*视频生成：输入提示词和参数*

![漫剧生成](screenshots/comic_generation.png)
*漫剧生成：分镜剧本编辑和批量生成*

---

## 🛠️ 打包发布

```bash
# 使用 PyInstaller 打包为单文件 exe
pip install pyinstaller
pyinstaller --onefile --windowed --name "AgnesAI-Video-Generator" main.py

# 打包产物在 dist/ 目录
# 可直接分发给他人使用
```

---

## ⚠️ 常见问题

### Q: 提示"401 认证失败"
检查 API Key 是否正确，API Base URL 是否为 `https://apihub.agnes-ai.com`。

### Q: 配置保存失败
确保数据目录有写入权限。可以点击"📁 选择目录"更换保存位置。

### Q: 视频生成超时
网络连接问题或 API 服务繁忙。请检查网络后重试。

### Q: 双击 exe 闪退
查看 `error.log` 文件获取错误详情。

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源，详见 LICENSE 文件。

---

## 🙏 致谢

- [Agnes AI](https://agnes-ai.com/) - 提供 AI 视频生成 API
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 跨平台 GUI 框架

---

## 📞 联系方式

如有问题或建议，欢迎提交 Issue。
