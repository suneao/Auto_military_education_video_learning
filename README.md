# 视频学习自动化脚本

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r video_auto_learner/requirements.txt
# 或直接安装
pip install aiohttp beautifulsoup4 requests
```

### 2. 获取课程数据（非必需步骤）
1. **登录考试平台**：访问 http://www.gaoxiaokaoshi.com
2. **进入课程页面**：登录后进入"我的课程"页面
3. **保存课程列表**：
   - 右键 → "另存为"
   - 保存全部并保存在程序目录下方
   - 保持文件结构和命名

### 3. 配置Cookie（三选一）

#### 方法一：使用现有Cookie（推荐）
直接运行脚本，脚本会自动：
- 检测现有Cookie（`config.json`或`fixed_config.json`）
- 修复Cookie格式问题
- 开始视频学习

```bash
python fixed_video_learner.py
```

#### 方法二：重新登录获取新Cookie
如果现有Cookie过期，请使用TUI重新登录：
1. 运行 `python video_learner_tui.py`
2. 选择 `配置Cookie` → `重新登录获取新Cookie`
3. 输入您的账号密码
4. 脚本会自动获取新Cookie并保存到`fixed_config.json`

**安全提示**：脚本不会保存您的密码，每次登录都需要输入

#### 方法三：手动配置Cookie
1. 获取Cookie（浏览器F12 → 应用 → Cookies）：
   - `ASP.NET_SessionId`
   - `.ASPXAUTH`
   - `Clerk`
   - `ZYLTheme`

2. 创建配置文件 `fixed_config.json`：
```json
{
  "cookies": {
    "ASP.NET_SessionId": "从浏览器获取的会话ID",
    ".ASPXAUTH": "从浏览器获取的认证令牌",
    "Clerk": "从浏览器获取的用户信息",
    "ZYLTheme": "Theme=blue&ScreenType=1280"
  },
  "base_url": "http://www.gaoxiaokaoshi.com",
  "update_interval_seconds": 61,
  "max_concurrent_videos": 5,
  "retry_attempts": 3
}
```

### 4. 文本用户界面 (TUI) - 推荐新手使用
```bash
# 启动交互式文本用户界面
python video_learner_tui.py
```

TUI提供完整的交互式菜单：
- 🛠️  Cookie配置向导（登录获取/文件加载/手动输入）
- 🚀  一键开始视频学习
- 📊  实时进度查看
- 🔗  网络和Cookie测试
- ⚙️  账号密码设置
- 📁  文件检查工具
- ❓  帮助文档

### 5. 运行脚本（高级用户）
```bash
# 直接运行修复版脚本
python fixed_video_learner.py

# 查看实时日志
tail -f fixed_video_learner.log
```

## 📊 脚本功能

### 自动流程
1. **Cookie检测** → 2. **课程解析** → 3. **参数获取** → 4. **并行学习** → 5. **完成退出**

### 并行处理
- 🔄 **并发处理**：同时处理多个视频（默认最多5个）
- ⏱️ **智能调度**：交错启动，每61秒提交一次进度
- 📈 **实时监控**：显示每个视频的剩余时间和累计提交时长
- 🔄 **错误重试**：自动重试失败的请求（最多3次）

### 日志输出
```
2025-12-23 22:31:03,751 - INFO - 发现未完成课程: 2.1 国家安全概述 (ID: 1298, 进度: 31/60分钟, 还需: 1740秒)
2025-12-23 22:31:04,336 - INFO - 视频 [2.1 国家安全概述] 第1次更新成功，累计提交: 61秒，还需: 1679秒
```

## 🔧 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| **Cookie无效** | 运行脚本会自动重新登录获取新Cookie |
| **"1280"不是一个有效的主题名称** | ✅ **已修复** - 使用修复版脚本 |
| **课程解析失败** | 检查`考试平台_files/LibraryStudyList.html`文件是否完整 |
| **网络连接失败** | 检查网络连接和防火墙设置 |
| **进度提交无响应** | 查看日志文件了解具体错误 |

### 调试工具
使用TUI内置的测试功能：
1. 运行 `python video_learner_tui.py`
2. 选择 `4) 🔗 测试连接` - 测试网络和Cookie
3. 选择 `6) 📁 检查文件` - 检查必需文件

或直接查看日志：
```bash
# 查看详细日志
less video_auto_learner.log
```

## 📁 文件说明

### 核心文件
- `video_learner_tui.py` - **文本用户界面 (TUI)**（推荐新手使用）
- `video_auto_learner.py` - **主脚本**（高级用户）
- `config.json` - 配置文件（自动生成）
- `video_auto_learner.log` - 运行日志

### 数据文件
- `考试平台_files/LibraryStudyList.html` - 课程列表（需手动保存）
- `考试平台_files/LibraryStudy.html` - 课程详情（自动生成）

### 文档工具
- `API_DOCUMENTATION.md` - API接口文档（技术参考）
- TUI内置帮助 - 运行 `python video_learner_tui.py` 选择 `7) ❓ 帮助`

## ⚠️ 注意事项

### 使用规范
1. **合理使用**：仅用于个人学习目的
2. **遵守规则**：尊重平台服务条款
3. **数据安全**：妥善保管Cookie信息
4. **网络礼仪**：避免高频请求影响服务器

### 技术限制
- **Cookie有效期**：通常为会话期间，过期需重新登录
- **网络要求**：需要稳定访问考试平台
- **运行时间**：取决于未完成视频总时长
- **并发限制**：默认5个并发，避免被封禁

### 停止脚本
- **正常停止**：按 `Ctrl+C`
- **断点续传**：重新运行会继续未完成的学习
- **日志查看**：所有进度记录在`video_auto_learner.log`

## 🆘 技术支持

### 获取帮助
1. **查看日志**：提供`video_auto_learner.log`文件内容
2. **描述问题**：具体错误信息和操作步骤
3. **检查文件**：确认课程列表HTML文件完整

### 联系开发者
- 📧 提供详细的错误日志
- 🔍 描述问题复现步骤
- 📋 附上相关配置文件（去除敏感信息）

## 📄 许可证
仅限个人学习使用，请遵守相关法律法规和平台规定。

## 🚀 快速启动

### 直接运行
```bash
# 启动文本用户界面 (TUI)
python video_learner_tui.py

# 或直接运行主脚本
python video_auto_learner.py
```

### 依赖安装
首次使用请安装依赖：
```bash
pip install aiohttp beautifulsoup4 requests
```

---

**最后更新**: 2025-12-23  
**脚本版本**: 修复版 v2.1 (优化版)  
**包含组件**: 修复版脚本 + 文本用户界面 (TUI)  
**测试状态**: ✅ 已验证可正常运行