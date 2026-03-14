# 巅峰极速车辆数据及排位计分车推荐 / RacingMaster-RankHelper

<div align="center">

一款专为《巅峰极速》国服玩家打造的智能工具，通过数据分析帮助你选出最优排位计分车辆组合。

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

### 🎯 排位车辆推荐（全新改进）
- **智能联赛系统**：支持14个联赛等级（新秀联赛1 → 巅峰联赛）
- **精确计分车辆配置**：每个联赛等级对应不同的计分车辆数量
- **优化布局**：改进推荐计分车表格布局，移除冗余列，信息更清晰
- **调教推荐**：新增调教推荐列，显示每辆车的最优调教参数
  - 支持多方案调教（如"调教1: 13232, 调教2: 23232"）
  - 支持带前缀调教（如"漂调教: 23332, 抓调教: 12332"）
  - 自动根据车辆阶位匹配对应调教数据
- **分组别推荐**：极限组、性能组、运动组独立推荐
- **全部推荐**：综合所有组别，按圈速总和排序
- **灵活调整**：支持手动调整计分车辆数量（适应赛季周限制）

### 💾 数据管理
- 从网站自动更新车辆数据库（圈速+调教数据）
- 重置车辆数据库功能，快速清空并重新获取数据
- **多账号数据导出**：一键导出所有账号的车库和当前组合数据（JSON格式）
- **选择性导入**：导入时可选择恢复全部或特定账号的数据
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

本工具仅供学习和研究使用，专为《巅峰极速》国服设计。使用本工具产生的任何后果由使用者自行承担。

## 🌏 适用范围

本程序仅针对《巅峰极速》国服（中国大陆服务器），数据来源于国服数据源。其他服务器的数据可能不兼容。

---

<div align="center">

如果这个项目对你有帮助，请给一个 ⭐️ Star！

Made with ❤️ for RacingMaster Players

</div>
