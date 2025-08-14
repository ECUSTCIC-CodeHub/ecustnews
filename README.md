# 华东理工大学新闻通知自动抓取脚本

## 功能说明
- 自动从华东理工大学新闻网站、学生处和教务处网站抓取近期通知
- 支持多个收件人邮箱配置
- 生成美观的HTML邮件格式
- 完整的日志记录功能
- 智能日期解析和链接处理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 邮箱配置 (config.json)
修改 `config.json` 文件中的SMTP配置：

```json
{
    "smtp": {
        "server": "smtp.qq.com",
        "port": 587,
        "username": "your_email@qq.com",
        "password": "your_app_password",
        "sender_email": "your_email@qq.com"
    },
    "days": 3
}
```

**注意：**
- 如果使用QQ邮箱，需要开启SMTP服务并使用授权码作为密码
- 如果使用其他邮箱，请相应修改server和port
- `days` 参数用于设置抓取多少天内的通知，默认为3天

### 2. 收件人配置 (emails.json)
修改 `emails.json` 文件添加收件人：

```json
[
    {
        "name": "张三",
        "email": "zhangsan@example.com"
    },
    {
        "name": "李四", 
        "email": "lisi@example.com"
    }
]
```

## 使用方法

### 手动运行
```bash
python news_scraper.py
```

### 定时任务
可以使用系统的定时任务功能：

**Windows (任务计划程序):**
1. 打开任务计划程序
2. 创建基本任务
3. 设置触发器（如每天上午9点）
4. 设置操作：启动程序 `python`，参数 `news_scraper.py`，起始于脚本目录

**Linux/Mac (crontab):**
```bash
# 每天上午9点执行
0 9 * * * cd /path/to/script && python news_scraper.py
```

## 日志文件
脚本运行时会生成 `news_scraper.log` 日志文件，记录运行状态和错误信息。

## 文件结构
```
ecustnews/
├── news_scraper.py     # 主脚本（包含学校新闻网、学生处和教务处抓取逻辑）
├── config.json         # 邮箱配置和抓取天数设置
├── emails.json         # 收件人列表
├── requirements.txt    # 依赖包
├── README.md          # 说明文档
└── news_scraper.log   # 日志文件（运行后生成）
```

## 常见问题

### 1. 邮件发送失败
- 检查SMTP配置是否正确
- 确认邮箱密码/授权码是否正确
- 检查网络连接

### 2. 抓取失败
- 检查网络连接
- 网站结构可能发生变化，需要更新解析代码

### 3. 日期解析错误
- 检查网站日期格式是否发生变化
- 查看日志文件获取详细错误信息

## 技术说明
- 使用 requests 库进行HTTP请求
- 使用 BeautifulSoup 解析HTML
- 支持HTML格式邮件
- 自动处理相对链接转换
- 完整的错误处理和日志记录