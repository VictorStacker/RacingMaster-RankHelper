# GitHub Release 发布清单

## 发布前检查

- [x] 清理临时文件和测试文件
- [x] 更新版本号到 1.3
- [x] 更新 CHANGELOG.md
- [x] 更新 RELEASE_NOTES.md
- [x] 打包 exe 文件

### 主要文件
1. **RacingMaster-RankHelper-v1.3.exe**
   - 位置: `dist/RacingMaster-RankHelper-v1.3.exe`
   - 这是用户需要下载的主程序

## 发布步骤

### 1. 确认版本号
所有文件版本号已统一为 `1.3`：
- `rm_rank/__init__.py`
- `rm_rank/config.py`
- `rm_rank/ui/main_window.py`（关于对话框）
- `pyproject.toml`

### 2. Release 信息

**Tag version**: `v1.3`

**Release title**: `RacingMaster-RankHelper v1.3 - 多账号导出修复与体验优化`

**Description**:
```markdown
# 🎉 RacingMaster-RankHelper v1.3

## ✨ 主要更新

### 🐛 修复
- 修复多账号数据导出问题（现在会导出所有账号的数据）
- 修复切换账号时车库下拉框不同步问题
- 修复状态栏账号显示消失问题

### 🎯 改进
- 账号管理新增上移/下移排序功能
- 车库新增总榜排名列（取代原本的车辆 ID）
- 推荐页「排名」改为「推荐序」，避免与总榜混淆
- 推荐页面记忆联赛等级选择
- 车库「删除」按钮改为「移出车库」
- 简化导入/导出菜单
- 简化数据更新进度对话框（完成后 5 秒自动关闭）
- 改善关于对话框内容

## 📥 下载

下载 `RacingMaster-RankHelper-v1.3.exe` 即可使用。

## 📋 适用范围

本程序仅针对《巅峰极速》国服（中国大陆服务器）。
```

### 3. 上传文件
- 拖拽 `dist/RacingMaster-RankHelper-v1.3.exe` 到 "Attach binaries" 区域

### 4. 发布选项
- [ ] Set as latest release ✅
- [ ] Create a discussion for this release（可选）
