# 贡献指南

感谢你考虑为本项目做出贡献！

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请创建一个 Issue 并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 截图（如果适用）
- 环境信息（操作系统、Python 版本等）

### 提出新功能

如果你有新功能的想法：

1. 先检查 Issues 中是否已有类似建议
2. 创建一个新的 Issue 描述你的想法
3. 等待维护者的反馈

### 提交代码

1. **Fork 仓库**
   ```bash
   # 点击 GitHub 页面右上角的 Fork 按钮
   ```

2. **克隆你的 Fork**
   ```bash
   git clone https://github.com/your-username/RacingMaster-RankHelper.git
   cd RacingMaster-RankHelper
   ```

3. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **安装开发依赖**
   ```bash
   poetry install
   ```

5. **进行修改**
   - 遵循现有的代码风格
   - 添加必要的测试
   - 更新文档（如果需要）

6. **运行测试**
   ```bash
   poetry run pytest
   ```

7. **提交更改**
   ```bash
   git add .
   git commit -m "描述你的更改"
   ```

   提交信息格式：
   - `feat: 添加新功能`
   - `fix: 修复 Bug`
   - `docs: 更新文档`
   - `style: 代码格式调整`
   - `refactor: 代码重构`
   - `test: 添加测试`
   - `chore: 构建/工具链更新`

8. **推送到你的 Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

9. **创建 Pull Request**
   - 访问原仓库页面
   - 点击 "New Pull Request"
   - 选择你的分支
   - 填写 PR 描述
   - 提交 PR

## 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 4 个空格缩进
- 最大行长度：88 字符（Black 默认）
- 使用类型注解

### 命名规范

- 类名：`PascalCase`
- 函数/变量：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：`_leading_underscore`

### 文档字符串

使用 Google 风格的文档字符串：

```python
def function_name(param1: str, param2: int) -> bool:
    """简短描述函数功能。
    
    详细描述（可选）。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        
    Returns:
        返回值的描述
        
    Raises:
        ValueError: 异常情况的描述
    """
    pass
```

### 测试

- 为新功能添加测试
- 确保所有测试通过
- 测试覆盖率应保持在 80% 以上

## 开发工具

### 代码格式化

```bash
poetry run black peak_speed tests
```

### 类型检查

```bash
poetry run mypy peak_speed
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_specific.py

# 查看覆盖率
poetry run pytest --cov=peak_speed
```

## Pull Request 检查清单

在提交 PR 之前，请确保：

- [ ] 代码遵循项目的代码规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] PR 描述详细说明了更改内容

## 行为准则

- 尊重所有贡献者
- 接受建设性的批评
- 专注于对项目最有利的事情
- 对社区成员表现出同理心

## 问题？

如果你有任何问题，可以：

- 创建一个 Issue
- 在 Pull Request 中提问
- 联系项目维护者

---

再次感谢你的贡献！🎉
