# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 配置模块
定义全局配置参数
"""

import os

# 基础 URL
BASE_URL = "https://nba.hupu.com"

# HTTP 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://nba.hupu.com/",
}

# 请求配置
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）
REQUEST_DELAY = 1.5   # 请求间隔时间（秒），避免频繁访问
MAX_RETRIES = 3       # 最大重试次数

# 赛季配置（最近5年）
SEASONS = [
    "2024-25",
    "2023-24",
    "2022-23",
    "2021-22",
    "2020-21",
]

# 球员统计数据类别（优先级排序：得分、篮板、助攻优先）
PLAYER_STATS_CATEGORIES = [
    {"name": "得分", "code": "pts", "priority": 1},
    {"name": "篮板", "code": "reb", "priority": 1},
    {"name": "助攻", "code": "asts", "priority": 1},
    {"name": "投篮", "code": "fgp", "priority": 2},
    {"name": "三分", "code": "tpp", "priority": 2},
    {"name": "罚球", "code": "ftp", "priority": 2},
    {"name": "盖帽", "code": "blk", "priority": 2},
    {"name": "抢断", "code": "stl", "priority": 2},
]

# 30支 NBA 球队代码映射
TEAMS = {
    # 东部联盟 - 大西洋赛区
    "celtics": "波士顿凯尔特人",
    "nets": "布鲁克林篮网",
    "knicks": "纽约尼克斯",
    "76ers": "费城76人",
    "raptors": "多伦多猛龙",
    # 东部联盟 - 中部赛区
    "bulls": "芝加哥公牛",
    "cavaliers": "克利夫兰骑士",
    "pistons": "底特律活塞",
    "pacers": "印第安纳步行者",
    "bucks": "密尔沃基雄鹿",
    # 东部联盟 - 东南赛区
    "hawks": "亚特兰大老鹰",
    "hornets": "夏洛特黄蜂",
    "heat": "迈阿密热火",
    "magic": "奥兰多魔术",
    "wizards": "华盛顿奇才",
    # 西部联盟 - 西北赛区
    "nuggets": "丹佛掘金",
    "timberwolves": "明尼苏达森林狼",
    "thunder": "俄克拉荷马城雷霆",
    "blazers": "波特兰开拓者",
    "jazz": "犹他爵士",
    # 西部联盟 - 太平洋赛区
    "warriors": "金州勇士",
    "clippers": "洛杉矶快船",
    "lakers": "洛杉矶湖人",
    "suns": "菲尼克斯太阳",
    "kings": "萨克拉门托国王",
    # 西部联盟 - 西南赛区
    "mavericks": "达拉斯独行侠",
    "rockets": "休斯顿火箭",
    "grizzlies": "孟菲斯灰熊",
    "pelicans": "新奥尔良鹈鹕",
    "spurs": "圣安东尼奥马刺",
}

# URL 模板
URLS = {
    "player_stats": "/stats/players/{category}",      # 球员统计
    "team_stats": "/stats/teams",                     # 球队统计
    "standings": "/standings",                        # 战绩排行
    "roster": "/players/{team_code}",                 # 球队球员名单
}

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# 分类子目录
OUTPUT_SUBDIRS = {
    "rosters": os.path.join(OUTPUT_DIR, "球队名单"),
    "player_stats": os.path.join(OUTPUT_DIR, "球员统计"),
    "team_stats": os.path.join(OUTPUT_DIR, "球队统计"),
    "standings": os.path.join(OUTPUT_DIR, "战绩排行"),
}

# 确保所有目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for subdir in OUTPUT_SUBDIRS.values():
    if not os.path.exists(subdir):
        os.makedirs(subdir)
