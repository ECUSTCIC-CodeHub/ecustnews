@echo off
chcp 65001 >nul
echo 华东理工大学新闻抓取脚本
echo ========================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show requests >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖包安装失败
        pause
        exit /b 1
    )
)

REM 运行脚本
echo 开始运行新闻抓取脚本...
echo.
python news_scraper.py

echo.
echo 脚本执行完成！
pause