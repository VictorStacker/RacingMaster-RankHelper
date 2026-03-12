# GitHub Release 发布清单

## 📋 发布前检查

- [x] 清理临时文件和测试文件
- [x] 更新版本号到 1.1.0
- [x] 添加应用图标
- [x] 打包 exe 文件
- [x] 验证 exe 文件大小和日期
- [x] 创建发布说明

## 📦 需要上传的文件

### 主要文件
1. **RacingMaster-RankHelper-v1.1.0.exe** (164.48 MB)
   - 位置: `dist/RacingMaster-RankHelper-v1.1.0.exe`
   - 这是用户需要下载的主程序

### 可选文件（源代码会自动打包）
2. **icon.png** - 应用图标（可选）
3. **RELEASE_NOTES.md** - 发布说明（可选）

## 🚀 GitHub Release 步骤

### 1. 创建新 Release
```
1. 访问 GitHub 仓库
2. 点击 "Releases" → "Draft a new release"
3. 填写以下信息：
```

### 2. Release 信息

**Tag version**: `v1.1.0`

**Release title**: `RacingMaster-RankHelper v1.1.0 - 调教推荐与数据修复`

**Description**: 
```markdown
# 🎉 RacingMaster-RankHelper v1.1.0

## ✨ 主要更新

### 新功能
- ✅ 推荐计分车布局改进
- ✅ 新增调教推荐功能
- ✅ 新增重置车辆数据库功能

### Bug 修复
- 🐛 修复调教数据解析错误（多方案、带前缀、特殊格式）
- 🐛 修复数据库路径配置问题

### 技术改进
- 🔧 统一数据库存储到用户目录
- 🔧 添加自定义应用图标
- 🔧 优化打包配置

## 📥 下载

下载 `RacingMaster-RankHelper-v1.1.0.exe` 即可使用。

## 📋 适用范围

**本程序仅适用于巅峰极速国服（中国服务器）**

## 🚀 使用说明

1. 下载并运行 exe 文件
2. 首次使用请点击"数据(D) → 更新数据库(U)"
3. 在"我的车库"添加车辆
4. 在"排位车辆推荐"查看推荐和调教

## 🙏 致谢

数据支持：[阿龙WayLong](https://waylongrank.top/index.html)

完整更新日志请查看 [CHANGELOG.md](https://github.com/VictorStacker/RacingMaster-RankHelper/blob/main/CHANGELOG.md)

---

Made with ❤️ for RacingMaster Players
```

### 3. 上传文件
- 拖拽 `dist/RacingMaster-RankHelper-v1.1.0.exe` 到 "Attach binaries" 区域

### 4. 发布选项
- [ ] Set as a pre-release (如果是测试版)
- [x] Set as the latest release (正式版)

### 5. 点击 "Publish release"

## 📝 发布后

1. 验证下载链接是否正常
2. 测试下载的 exe 文件是否可以运行
3. 在 README.md 中更新下载链接
4. 通知用户新版本发布

## 🔗 相关链接

- GitHub 仓库: https://github.com/VictorStacker/RacingMaster-RankHelper
- 数据来源: https://waylongrank.top/index.html

## ⚠️ 注意事项

- exe 文件不包含任何个人数据
- 用户首次运行会在 `C:\Users\[用户名]\.racingmaster-rankhelper\` 创建数据库
- 每个用户的数据完全独立
