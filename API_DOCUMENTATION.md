# 考试平台视频学习API文档

## 概述
本文档记录了考试平台（gaoxiaokaoshi.com）视频学习相关的API接口和参数。

## 核心API接口

### 1. 课程列表页面
- **URL**: `http://www.gaoxiaokaoshi.com/Study/LibraryStudyList.aspx`
- **方法**: GET
- **功能**: 显示所有课程列表
- **返回**: HTML页面，包含课程信息表格

### 2. 课程详情页面
- **URL**: `http://www.gaoxiaokaoshi.com/Study/LibraryStudy.aspx`
- **方法**: GET
- **参数**:
  - `Id`: 课程ID (例如: 1298)
  - `PlanId`: 计划ID (固定为32)
- **功能**: 显示课程学习页面，包含视频播放器和隐藏字段
- **返回**: HTML页面，包含视频播放器和隐藏字段

### 3. 学习进度更新接口
- **URL**: `http://www.gaoxiaokaoshi.com/Study/updateTime.ashx`
- **方法**: GET
- **参数**:
  - `Id`: 学习记录ID (hidNewId，每次访问课程详情页面时动态生成)
  - `pTime`: 当前累计学习秒数
  - `Mins`: 通过线 (固定为1)
  - `refId`: 课程ID (固定值)
  - `StudentId`: 学生ID (固定值)
  - `StydyTime`: 已学习时间 (秒，注意拼写为"StydyTime"而不是"StudyTime")
  - `SessionId`: 会话ID (ASP.NET_SessionId的值)
- **功能**: 提交学习进度
- **返回**: 空响应或JSON格式的响应

## Cookie要求

### 必需Cookie
1. **ASP.NET_SessionId**
   - 格式: 字符串
   - 作用: 用户会话标识
   - 来源: 登录成功后服务器设置

2. **ZYLTheme**
   - 格式: `Theme=blue&ScreenType=`
   - 注意: ScreenType参数的值不能包含引号，服务器会对引号进行错误解析
   - 有效格式: `Theme=blue&ScreenType=1280`
   - 无效格式: `Theme=blue&ScreenType="1280"` (会导致"1280"不是一个有效的主题名称"错误)

3. **Clerk**
   - 格式: URL编码的用户信息字符串
   - 包含: ClerkID, UserName, ClerkName, Pwd等用户信息

4. **p_h5_u**
   - 格式: GUID字符串
   - 作用: 用户标识

5. **selectedStreamLevel**
   - 格式: 字符串 (例如: "SD")
   - 作用: 视频流级别选择

### Cookie获取流程
1. 访问登录页面: `/Login.aspx`
2. 提交登录表单到: `/HidLogin.aspx`
3. 登录成功后会设置上述Cookie

## 错误处理

### 常见错误
1. **500错误 - "1280"不是一个有效的主题名称**
   - **原因**: ZYLTheme Cookie中的ScreenType参数值包含引号
   - **解决方案**: 确保ZYLTheme格式为 `Theme=blue&ScreenType=1280` 而不是 `Theme=blue&ScreenType="1280"`

2. **404错误 - 找不到资源**
   - **原因**: API路径错误
   - **解决方案**: 确保使用正确的URL路径 `/Study/updateTime.ashx` 而不是 `/updateTime.ashx`

3. **Cookie无效**
   - **原因**: Cookie过期或格式错误
   - **解决方案**: 重新登录获取新Cookie

## 请求头要求

### 必需请求头
```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Accept-Encoding: gzip, deflate
Connection: keep-alive
```

### Referer头
- 访问课程详情页面时: `Referer: http://www.gaoxiaokaoshi.com/Study/LibraryStudyList.aspx`
- 提交学习进度时: `Referer: http://www.gaoxiaokaoshi.com/Study/LibraryStudy.aspx?Id={course_id}&PlanId=32`

## 隐藏字段解析

课程详情页面包含以下隐藏字段：

```html
<input type="hidden" name="hidNewId" id="hidNewId" value="" />
<input type="hidden" name="hidRefId" id="hidRefId" value="" />
<input type="hidden" name="hidStudentId" id="hidStudentId" value="YOUR_STUDENT_ID_HERE" />
<input type="hidden" name="hidPassLine" id="hidPassLine" value="1" />
<input type="hidden" name="hidStudyTime" id="hidStudyTime" value="0" />
<input type="hidden" name="hidSessionID" id="hidSessionID" value="" />
```

## 工作流程

### 完整的学习流程
1. **登录认证**
   - 获取有效的Cookie集合

2. **获取课程列表**
   - 解析HTML页面中的未完成课程

3. **获取课程参数**
   - 为每个未完成课程访问课程详情页面
   - 提取隐藏字段值

4. **提交学习进度**
   - 每61秒提交一次学习进度
   - 使用提取的参数调用updateTime.ashx

5. **并行处理**
   - 支持同时处理多个视频课程
   - 交错启动避免请求过于集中

## 自动化脚本实现要点

### 1. Cookie管理
- 支持从配置文件加载Cookie
- 支持自动登录获取新Cookie
- 修复ZYLTheme格式问题

### 2. 错误重试
- 网络错误时自动重试
- 指数退避策略
- 最大重试次数限制

### 3. 并发控制
- 限制并发连接数
- 交错启动避免峰值
- 每个视频独立计时器

### 4. 日志记录
- 详细的运行日志
- 错误信息记录
- 进度跟踪

## 测试工具

### 可用测试脚本
1. **Cookie测试**: 验证Cookie有效性
2. **API测试**: 测试updateTime.ashx接口
3. **参数提取测试**: 测试课程参数获取
4. **完整流程测试**: 测试整个自动化流程

## 注意事项

### 安全提示
- 不要将包含敏感信息的Cookie提交到版本控制系统
- 定期更新过期Cookie
- 遵守平台使用规则

### 性能优化
- 合理设置请求间隔
- 避免过于频繁的请求
- 使用连接池管理HTTP连接

### 故障排除
1. 检查Cookie是否过期
2. 验证ZYLTheme格式
3. 确认API路径正确
4. 查看服务器响应状态码
5. 分析错误响应内容

## 版本历史
- v1.0: 初始文档，基于2025年12月23日的测试结果
- 更新: 修复了ZYLTheme格式问题和API路径问题