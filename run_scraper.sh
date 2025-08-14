#!/bin/bash

echo "华东理工大学新闻抓取脚本"
echo "========================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖包..."
if ! python3 -c "import requests, bs4" &> /dev/null; then
    echo "正在安装依赖包..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误：依赖包安装失败"
        exit 1
    fi
fi

# 运行脚本
echo "开始运行新闻抓取脚本..."
echo
python3 news_scraper.py

echo
echo "脚本执行完成！"