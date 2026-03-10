# 巅峰极速车辆数据及排位计分车推荐 / RacingMaster-RankHelper

<div align="center">

[简体中文](README.md) | [English](README_EN.md)

一个专为《巅峰极速》游戏玩家设计的数据驱动决策支持工具，帮助优化排位赛车辆选择策略。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)

</div>

## ✨ 功能特性

### 🏆 车辆排行榜
- 实时查看所有车辆的圈速数据
- 按组别筛选（极限组/性能组/运动组）
- 支持按圈速、阶数、组别排序
- 清晰的表格展示，一目了然

### 🚗 我的车库
- 多账号管理，轻松切换
- 添加/删除车辆，自定义阶数
- 内联调整按钮，快速升阶
- 自动按圈速排序

### 🎯 排位车辆推荐
- **智能联赛系统**：支持14个联赛等级（新秀联赛1 → 巅峰联赛）
- **精确计分车辆配置**：每个联赛等级对应不同的计分车辆数量
- **分组别推荐**：极限组、性能组、运动组独立推荐
- **全部推荐**：综合所有组别，按圈速总和排序
- **灵活调整**：支持手动调整计分车辆数量（适应赛季周限制）

### 💾 数据管理
- 从网站自动更新车辆数据库
- 导入/导出车辆和车库数据（JSON格式）
- SQLite本地存储，快速可靠

## 📸 界面预览

### 车辆排行榜
实时查看所有车辆的圈速数据，支持按组别筛选和排序。

![车辆排行榜](screenshots/screenshot-ranking.png)

### 我的车库
管理你的车辆收藏，支持多账号、添加删除、快速调整阶数。

![我的车库](screenshots/screenshot-garage.png)

### 排位车辆推荐
根据联赛等级智能推荐最优计分车辆组合，助你冲击排行榜。

![排位车辆推荐](screenshots/screenshot-recommendation.png)

## 🚀 快速开始

### 前置要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/your-username/RacingMaster-RankHelper.git
cd RacingMaster-RankHelper
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

或使用 Poetry：
```bash
poetry install
```

3. **安装 Playwright 浏览器**（用于数据更新）
```bash
playwright install chromium
```

### 启动应用

**图形界面（推荐）：**
```bash
python run_gui.py
```

**命令行界面：**
```bash
python run.py
```

## 📖 使用指南

### 1. 更新车辆数据库
首次使用时，从菜单栏选择 `数据 → 更新数据库` 来获取最新的车辆圈速数据。

### 2. 管理车库
- 在"我的车库"标签页中，点击"添加车辆"按钮
- 从下拉列表中选择车辆和阶数
- 使用内联"调整"按钮快速升阶
- 支持多账号管理，可在不同账号间切换

### 3. 生成推荐
- 切换到"排位车辆推荐"标签页
- 选择你的最高联赛等级
- 系统自动匹配对应的计分车辆数量
- 点击"生成推荐"查看最优组合
- 可手动调整计分车辆数量以适应特殊情况

### 4. 联赛等级说明

| 联赛等级 | 极限组 | 性能组 | 运动组 | 总计 |
|---------|-------|-------|-------|------|
| 新秀联赛1 | 2 | 2 | 2 | 6 |
| 新秀联赛2 | 3 | 3 | 3 | 9 |
| 新秀联赛3 | 4 | 4 | 4 | 12 |
| 新秀联赛4 | 5 | 5 | 5 | 15 |
| 精英联赛1 | 6 | 6 | 6 | 18 |
| 精英联赛2 | 7 | 6 | 6 | 19 |
| 精英联赛3 | 7 | 7 | 6 | 20 |
| 精英联赛4 | 7 | 7 | 7 | 21 |
| 精英联赛5 | 8 | 7 | 7 | 22 |
| 精英联赛6 | 8 | 8 | 7 | 23 |
| 精英联赛7 | 8 | 8 | 8 | 24 |
| 精英联赛8 | 9 | 8 | 8 | 25 |
| 精英联赛9 | 9 | 9 | 8 | 26 |
| 巅峰联赛 | 9 | 9 | 9 | 27 |

## 🏗️ 项目结构

```
peak-speed-ranking/
├── peak_speed/              # 主应用程序代码
│   ├── models/              # 数据模型（数据类和数据库模型）
│   ├── repositories/        # 数据访问层（车辆、车库、账号）
│   ├── engines/             # 业务逻辑引擎（排名、推荐）
│   ├── crawler/             # 网页数据爬虫
│   ├── ui/                  # PyQt6 图形界面
│   │   ├── main_window.py   # 主窗口
│   │   ├── ranking_view.py  # 排行榜视图
│   │   ├── garage_view.py   # 车库视图
│   │   └── recommendation_view.py  # 推荐视图
│   ├── io/                  # 数据导入导出
│   └── main.py              # 应用程序入口
├── tests/                   # 测试代码
├── run_gui.py               # GUI启动脚本
├── run.py                   # CLI启动脚本
└── pyproject.toml           # 项目配置
```

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **GUI框架**: PyQt6
- **数据库**: SQLite + SQLAlchemy ORM
- **网页爬虫**: Playwright
- **测试**: pytest + Hypothesis
- **依赖管理**: Poetry

## 🤝 贡献

欢迎贡献代码、报告问题或提出新功能建议！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 车辆数据来源：[阿龙WayLong](https://waylongrank.top/index.html)
- 感谢所有为本项目做出贡献的开发者

## ⚠️ 免责声明

本工具仅供学习和研究使用。使用本工具产生的任何后果由使用者自行承担。

---

<div align="center">

如果这个项目对你有帮助，请给一个 ⭐️ Star！

Made with ❤️ by the community

</div>
 
