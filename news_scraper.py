#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华东理工大学新闻网站通知抓取脚本
自动抓取今日通知并发送到指定邮箱
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import datetime
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class NewsScraperECUST:
    def __init__(self, config_file='config.json', emails_file='emails.json'):
        """初始化爬虫"""
        self.config_file = config_file
        self.emails_file = emails_file
        self.config = self.load_config()
        self.emails = self.load_emails()
        
        # 学校新闻网站
        self.base_url = "https://news.ecust.edu.cn"
        self.news_url = "https://news.ecust.edu.cn/16/list.htm"
        
        # 学生处网站
        self.student_base_url = "https://student.ecust.edu.cn"
        self.student_news_url = "https://student.ecust.edu.cn/1048/list.htm"
        
        # 教务处网站
        self.jwc_base_url = "https://jwc.ecust.edu.cn"
        self.jwc_news_url = "https://jwc.ecust.edu.cn/main.htm"
        
        # 代理设置
        self.proxies = None
        if 'proxy' in self.config and self.config['proxy'].get('enabled', False):
            proxy_config = self.config['proxy']
            proxy_url = proxy_config.get('url', '')
            proxy_username = proxy_config.get('username', '')
            proxy_password = proxy_config.get('password', '')
            
            if proxy_url:
                # 如果有用户名和密码，则添加到代理URL中
                if proxy_username and proxy_password:
                    # 解析代理URL
                    from urllib.parse import urlparse, urlunparse
                    parsed = urlparse(proxy_url)
                    netloc = f"{proxy_username}:{proxy_password}@{parsed.netloc}"
                    proxy_url = urlunparse((parsed.scheme, netloc, parsed.path, 
                                           parsed.params, parsed.query, parsed.fragment))
                
                self.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logging.info(f"已启用代理: {proxy_url.replace(proxy_password, '****') if proxy_password else proxy_url}")
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"配置文件 {self.config_file} 不存在")
            return {}
    
    def load_emails(self):
        """加载邮箱列表"""
        try:
            with open(self.emails_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"邮箱文件 {self.emails_file} 不存在")
            return []
    
    def get_news_list(self):
        """获取学校新闻网站的新闻列表"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(self.news_url, headers=headers, timeout=10, proxies=self.proxies)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            # 查找新闻列表容器
            news_list = soup.find('ul', class_='news_list list2')
            if not news_list:
                logging.warning("未找到新闻列表容器")
                return news_items
            
            # 提取每条新闻
            items = news_list.find_all('li', class_='news')
            for item in items:
                try:
                    # 提取标题和链接
                    title_span = item.find('span', class_='news_title')
                    if not title_span:
                        continue
                    
                    title_link = title_span.find('a')
                    if not title_link:
                        continue
                    
                    title = title_link.get('title')
                    link = title_link.get('href')
                    
                    # 处理相对链接
                    if link and link.startswith('/'):
                        link = self.base_url + link
                    elif link and not link.startswith('http'):
                        link = self.base_url + '/' + link
                    
                    # 提取日期 - 新的日期格式解析
                    news_meta = item.find('span', class_='news_meta')
                    if not news_meta:
                        continue
                    
                    # 提取日和年月
                    meta_day = news_meta.find('span', class_='meta_day')
                    meta_year = news_meta.find('span', class_='meta_year')
                    
                    if not meta_day or not meta_year:
                        continue
                    
                    day = meta_day.get_text(strip=True)
                    year_month = meta_year.get_text(strip=True)  # 格式如 "2025.08"
                    
                    try:
                        # 解析年月日
                        year, month = year_month.split('.')
                        news_date = datetime.datetime(int(year), int(month), int(day)).date()
                    except (ValueError, AttributeError):
                        logging.warning(f"日期解析失败: {day} {year_month}")
                        continue
                    
                    news_items.append({
                        'title': title,
                        'link': link,
                        'date': news_date,
                        'source': '学校新闻网'
                    })
                    
                except Exception as e:
                    logging.warning(f"解析新闻项时出错: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            logging.error(f"获取学校新闻列表失败: {e}")
            return []
            
    def get_student_news_list(self):
        """获取学生处网站的新闻列表"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(self.student_news_url, headers=headers, timeout=10, proxies=self.proxies)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            
            # 查找指定的新闻列表容器
            col_news_con = soup.find('div', class_='col_news_con')
            if col_news_con:
                col_news_list = col_news_con.find('div', class_='col_news_list listcon')
                if col_news_list:
                    wp_news = col_news_list.find('div', id='wp_news_w6')
                    if wp_news:
                        news_list = wp_news.find('ul', class_='news_list list2')
                        if news_list:
                            # 找到了指定的新闻列表容器
                            news_lists = [news_list]
                        else:
                            logging.warning("未找到学生处新闻列表容器 (news_list list2)")
                            return news_items
                    else:
                        logging.warning("未找到学生处新闻列表容器 (wp_news_w6)")
                        return news_items
                else:
                    logging.warning("未找到学生处新闻列表容器 (col_news_list)")
                    return news_items
            else:
                logging.warning("未找到学生处新闻列表容器 (col_news_con)")
                return news_items
            
            # 遍历所有找到的新闻列表
            for news_list in news_lists:
                # 提取每条新闻
                items = news_list.find_all('li')
                for item in items:
                    try:
                        # 提取标题和链接 - 尝试多种可能的结构
                        title_link = None
                        
                        # 方式1: 通过 span.news_title > a
                        title_span = item.find('span', class_='news_title')
                        if title_span:
                            title_link = title_span.find('a')
                        
                        # 方式2: 直接查找 a 标签
                        if not title_link:
                            title_link = item.find('a')
                        
                        if not title_link:
                            continue
                        
                        title = title_link.get('title')
                        if not title:
                            title = title_link.get_text(strip=True)
                        
                        link = title_link.get('href')
                        if not link:
                            continue
                        
                        # 处理相对链接
                        if link.startswith('/'):
                            link = self.student_base_url + link
                        elif not link.startswith('http'):
                            link = self.student_base_url + '/' + link
                        
                        # 直接从 news_meta 标签获取日期
                        news_date = None
                        news_meta = item.find('span', class_='news_meta')
                        
                        if news_meta:
                            date_text = news_meta.get_text(strip=True)
                            # 处理格式为 "2023-11-01" 的日期
                            try:
                                year, month, day = date_text.split('-')
                                news_date = datetime.datetime(int(year), int(month), int(day)).date()
                            except (ValueError, AttributeError):
                                logging.debug(f"日期解析失败: {date_text}")
                        
                        # 如果无法从 news_meta 获取日期，尝试从链接中提取
                        if not news_date and link:
                            # 从链接中提取日期 (格式如 /2023/1101/c1048a162142/page.htm)
                            date_match = re.search(r'/(\d{4})/(\d{2})(\d{2})/', link)
                            if date_match:
                                try:
                                    year = int(date_match.group(1))
                                    month = int(date_match.group(2))
                                    day = int(date_match.group(3))
                                    news_date = datetime.datetime(year, month, day).date()
                                except (ValueError, IndexError):
                                    logging.debug(f"从链接提取日期失败: {link}")
                        
                        # 如果所有方法都无法提取日期，使用当前日期
                        if not news_date:
                            news_date = datetime.date.today()
                        
                        news_items.append({
                            'title': title,
                            'link': link,
                            'date': news_date,
                            'source': '学生处'
                        })
                        
                    except Exception as e:
                        logging.warning(f"解析学生处新闻项时出错: {e}")
                        continue
            
            return news_items
            
        except Exception as e:
            logging.error(f"获取学生处新闻列表失败: {e}")
            return []
    
    def get_jwc_news_list(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(self.jwc_news_url, headers=headers, timeout=10, proxies=self.proxies)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            news_items = []
            # 直接找所有 class="pan7" 的新闻单元格
            for td in soup.find_all('td', class_='pan7'):
                link_tag = td.find('a')
                if not link_tag:
                    continue

                title = link_tag.get('title') or link_tag.get_text(strip=True)
                href = link_tag.get('href')
                if href.startswith('/'):
                    full_link = self.jwc_base_url + href
                elif 'news.ecust.edu.cn' in href:
                    continue
                else:
                    full_link = self.jwc_base_url + '/' + href

                # —— 改这里：从嵌套 table 的 tr 中获取日期 —— 
                tr = td.find('tr')  # 找嵌套的 tr
                news_date = None
                if tr:
                    tds_inner = tr.find_all('td')
                    if len(tds_inner) >= 2:
                        date_text = tds_inner[1].get_text(strip=True)
                        try:
                            year, month, day = map(int, date_text.split('-'))
                            news_date = datetime.date(year, month, day)
                        except Exception:
                            pass

                if not news_date:
                    # 兜底：从链接提取日期
                    news_date = self._extract_date_from_link(href)

                news_items.append({
                    'title': title,
                    'link': full_link,
                    'date': news_date,
                    'source': '教务处'
                })

            return news_items
        except Exception as e:
            logging.error(f"获取教务处新闻列表失败: {e}")
            return []

    
    def _extract_date_from_link(self, href):
        """从链接中提取日期"""
        # 从链接中提取日期 (格式如 /2025/0724/c3938a181097/page.htm)
        date_match = href.split('/')
        if len(date_match) >= 3:
            try:
                year = int(date_match[1])
                month_day = date_match[2]
                month = int(month_day[:2])
                day = int(month_day[2:4])
                return datetime.datetime(year, month, day).date()
            except (ValueError, IndexError):
                # 如果无法从链接中提取日期，则使用当前日期
                logging.warning(f"无法从链接中提取日期: {href}")
        
        return datetime.date.today()
    
    def filter_recent_news(self, news_items):
        """筛选今日的新闻"""
        days = self.config['days']
        today = datetime.date.today()
        cutoff_date = today - datetime.timedelta(days)
        
        recent_news = []
        for item in news_items:
            if item['date'] >= cutoff_date:
                recent_news.append(item)
        
        # 按日期降序排列
        recent_news.sort(key=lambda x: x['date'], reverse=True)
        return recent_news
    
    def generate_email_content(self, news_items):
        """生成邮件内容"""
        if not news_items:
            return "今日暂无新通知。"
        
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_content = f"""
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; text-align: center; }}
        .news-item {{ margin: 15px 0; padding: 15px; border-left: 4px solid #007bff; background-color: #f9f9f9; }}
        .news-title {{ font-size: 16px; font-weight: bold; margin-bottom: 5px; }}
        .news-date {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .news-link {{ color: #007bff; text-decoration: none; }}
        .footer {{ margin-top: 30px; padding: 20px; background-color: #f4f4f4; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>华东理工大学今日通知</h2>
        <p>自动抓取时间: {current_time}</p>
    </div>
"""
        
        for item in news_items:
            source = item.get('source', '学校新闻网')  # 默认为学校新闻网
            html_content += f"""
            <div class="news-item">
                <div class="news-title">{item['title']}</div>
                <div class="news-date">发布日期: {item['date']} | 来源: {source}</div>
                <div><a href="{item['link']}" class="news-link">查看详情</a></div>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p>此邮件由自动化脚本发送，请勿回复。</p>
                <p>如需停止接收，请联系管理员。</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def send_email(self, content, news_count):
        """发送邮件"""
        if not self.config.get('smtp'):
            logging.error("SMTP配置不存在")
            return False
        
        smtp_config = self.config['smtp']
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{smtp_config['sender_email']}"
            msg['Subject'] = f"华东理工大学今日通知 ({news_count}条)"
            
            # 添加HTML内容
            html_part = MIMEText(content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 连接SMTP服务器
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            server.login(smtp_config['username'], smtp_config['password'])
            
            # 发送给每个收件人
            success_count = 0
            for email_info in self.emails:
                try:
                    msg['To'] = f"{email_info['name']} <{email_info['email']}>"
                    server.send_message(msg)
                    logging.info(f"邮件发送成功: {email_info['email']}")
                    success_count += 1
                    del msg['To']  # 删除To字段，为下一个收件人准备
                except Exception as e:
                    logging.error(f"发送邮件到 {email_info['email']} 失败: {e}")
            
            server.quit()
            logging.info(f"邮件发送完成，成功 {success_count}/{len(self.emails)} 个")
            return success_count > 0
            
        except Exception as e:
            logging.error(f"发送邮件失败: {e}")
            return False
    
    def check_proxy(self):
        """检查代理是否可用"""
        if not self.proxies:
            return True
            
        test_url = "https://www.baidu.com"
        try:
            logging.info("正在测试代理连接...")
            response = requests.get(test_url, proxies=self.proxies, timeout=5)
            if response.status_code == 200:
                logging.info("代理连接测试成功")
                return True
            else:
                logging.warning(f"代理连接测试失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"代理连接测试失败: {e}")
            return False
        
    def run(self):
        """运行主程序"""
        logging.info("开始抓取华东理工大学新闻...")
        
        # 如果启用了代理，先测试代理是否可用
        if self.proxies and not self.check_proxy():
            logging.error("代理不可用，程序退出")
            return
        
        all_news_items = []
        
        # 获取学校新闻网站的新闻列表
        school_news = self.get_news_list()
        if school_news:
            logging.info(f"获取到学校新闻网站 {len(school_news)} 条新闻")
            all_news_items.extend(school_news)
        else:
            logging.warning("未获取到学校新闻网站的新闻")
        
        # 获取学生处网站的新闻列表
        student_news = self.get_student_news_list()
        if student_news:
            logging.info(f"获取到学生处网站 {len(student_news)} 条新闻")
            all_news_items.extend(student_news)
        else:
            logging.warning("未获取到学生处网站的新闻")
        
        # 获取教务处网站的新闻列表
        jwc_news = self.get_jwc_news_list()
        if jwc_news:
            logging.info(f"获取到教务处网站 {len(jwc_news)} 条新闻")
            all_news_items.extend(jwc_news)
        else:
            logging.warning("未获取到教务处网站的新闻")
        
        if not all_news_items:
            logging.warning("未获取到任何新闻")
            return
        
        logging.info(f"总共获取到 {len(all_news_items)} 条新闻")
        
        # 筛选今日新闻
        recent_news = self.filter_recent_news(all_news_items)
        logging.info(f"筛选出今日新闻 {len(recent_news)} 条")
        
        # 生成邮件内容
        email_content = self.generate_email_content(recent_news)
        
        # 只有在有新通知时才发送邮件
        if recent_news and self.emails:
            self.send_email(email_content, len(recent_news))
        elif not recent_news:
            logging.info("今日暂无新通知，不发送邮件")
        else:
            logging.warning("没有配置收件人邮箱")
        
        logging.info("程序执行完成")

def main():
    """主函数"""
    scraper = NewsScraperECUST()
    scraper.run()

if __name__ == "__main__":
    main()