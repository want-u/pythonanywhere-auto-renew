# PythonAnywhere 自动续期工具

这个项目用于自动点击 PythonAnywhere 网页上的 "Run until 3 months from today" 按钮，确保免费网站保持运行状态。

## 功能特点

- 🤖 自动化登录 PythonAnywhere
- 🔄 自动点击续期按钮
- ⏰ 每两个月自动执行一次（通过 GitHub Actions）
- 🔒 使用 GitHub Secrets 安全存储凭证
- 📸 失败时自动保存截图用于调试

## 设置步骤

### 1. Fork 或克隆此仓库

```bash
git clone <your-repo-url>
cd pythonanywhere-auto-renew
```

### 2. 配置 GitHub Secrets

在 GitHub 仓库中设置以下 Secrets：

1. 进入仓库的 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下两个 secrets：
   - `PYTHONANYWHERE_USERNAME`: 你的 PythonAnywhere 用户名
   - `PYTHONANYWHERE_PASSWORD`: 你的 PythonAnywhere 密码

### 3. 本地测试（可选）

如果你想在本地测试脚本：

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 设置环境变量并运行（Windows使用 set 而不是 export）
# Windows PowerShell:
$env:PYTHONANYWHERE_USERNAME="your_username"
$env:PYTHONANYWHERE_PASSWORD="your_password"
python pythonanywhere_auto_renew.py

# Linux/macOS:
export PYTHONANYWHERE_USERNAME="your_username"
export PYTHONANYWHERE_PASSWORD="your_password"
python pythonanywhere_auto_renew.py

# 如果想看到浏览器操作过程（本地测试），可以设置：
$env:HEADLESS="false"  # Windows
export HEADLESS=false  # Linux/macOS
```

## 技术实现

1. **GitHub Actions 定时任务**: 每两个月的第1天自动触发（1月、3月、5月、7月、9月、11月）
2. **双重策略**:
   - **优先使用API**: 尝试通过HTTP请求直接调用续期接口
   - **浏览器自动化**: 如果API不可用，使用Playwright自动点击按钮
3. **安全存储**: 凭证通过 GitHub Secrets 安全存储，不会暴露在代码中

## 执行计划

脚本会在以下日期自动执行：
- 1月1日
- 3月1日
- 5月1日
- 7月1日
- 9月1日
- 11月1日

你也可以在 GitHub Actions 页面手动触发执行。

## 故障排除

如果脚本执行失败：

1. 检查 GitHub Actions 日志
2. 查看自动上传的错误截图和页面源码
3. 确认 PythonAnywhere 网站结构是否有变化
4. 验证凭证是否正确

## 工作原理

脚本会：
1. **优先尝试API方式**：尝试通过HTTP请求直接调用续期接口（更快更稳定）
2. **回退到浏览器自动化**：如果API不可用，使用Playwright自动点击按钮
3. **自动检测API**：浏览器模式下会监听网络请求，如果发现API端点会自动记录

## 注意事项

- ⚠️ 免费账户需要每3个月至少登录一次，此脚本每2个月执行一次以确保安全
- ⚠️ 脚本会自动根据用户名构建webapp ID（格式：`{username}_pythonanywhere_com`）
- ⚠️ 如果API方式可用，脚本会自动使用API，无需浏览器，执行更快

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

