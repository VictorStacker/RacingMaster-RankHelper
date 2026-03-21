# 构建 Windows 可执行文件

## 方法 1: 使用 PyInstaller（推荐）

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 构建可执行文件

```bash
pyinstaller RacingMaster-RankHelper.spec
```

或者使用命令行：

```bash
pyinstaller --name=RacingMaster-RankHelper --windowed --onefile run_gui.py
```

### 3. 查找生成的文件

可执行文件位于: `dist/RacingMaster-RankHelper-v1.5.exe`

## 方法 2: 使用 cx_Freeze

### 1. 安装 cx_Freeze

```bash
pip install cx_Freeze
```

### 2. 创建 setup.py

```python
from cx_Freeze import setup, Executable

setup(
    name="RacingMaster-RankHelper",
    version="1.1.0",
    description="巅峰极速车辆数据及排位计分车推荐",
    executables=[Executable("run_gui.py", base="Win32GUI", target_name="RacingMaster-RankHelper.exe")]
)
```

### 3. 构建

```bash
python setup.py build
```

## 打包参数说明

- `--windowed` / `--noconsole`: 不显示控制台窗口（GUI 应用）
- `--onefile`: 打包成单个 .exe 文件
- `--name`: 指定可执行文件名称
- `--icon`: 指定图标文件（.ico 格式）
- `--add-data`: 添加额外的数据文件

## 注意事项

1. **文件大小**: 单文件打包会比较大（约 100-200 MB），因为包含了所有依赖
2. **启动速度**: 单文件打包的启动速度会稍慢，因为需要解压
3. **杀毒软件**: 某些杀毒软件可能会误报，需要添加信任
4. **Playwright**: 如果使用数据更新功能，需要确保 Playwright 浏览器正确打包

## 优化建议

### 减小文件大小

使用 `--onedir` 代替 `--onefile`，生成文件夹形式的分发包：

```bash
pyinstaller --name=RacingMaster-RankHelper --windowed run_gui.py
```

### 排除不需要的模块

在 .spec 文件中添加 `excludes` 参数：

```python
excludes=['matplotlib', 'numpy', 'pandas']  # 如果不需要这些库
```

## 测试

构建完成后，请测试以下功能：

- [ ] GUI 正常启动
- [ ] 车辆排行榜显示正常
- [ ] 车库管理功能正常
- [ ] 推荐系统功能正常
- [ ] 数据导入导出功能正常
- [ ] 数据库更新功能正常（需要网络）

## 分发

将生成的 .exe 文件分发给用户时，建议：

1. 创建一个 Release 包，包含：
   - RacingMaster-RankHelper.exe
   - README.md（使用说明）
   - LICENSE（许可证）

2. 在 GitHub Releases 中发布

3. 提供 SHA256 校验和，确保文件完整性

## 故障排除

### 问题 1: 缺少模块

如果运行时提示缺少模块，在 .spec 文件的 `hiddenimports` 中添加：

```python
hiddenimports=['missing_module_name']
```

### 问题 2: 无法启动

尝试使用 `--console` 参数重新打包，查看错误信息：

```bash
pyinstaller --name=RacingMaster-RankHelper --console --onefile run_gui.py
```

### 问题 3: Playwright 浏览器问题

Playwright 的浏览器文件较大，可能需要单独处理。建议用户首次运行时手动安装：

```bash
playwright install chromium
```
