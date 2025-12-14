# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - ESPN 爬虫模块
从 ESPN 网站爬取 NBA 数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from request_handler import get_page
from parsers.espn import ESPNRosterParser, ESPNStatsParser, ESPNStandingsParser, ESPNTeamStatsParser
from data_cleaner import DataCleaner
from storage import CSVStorage
from config import OUTPUT_SUBDIRS


# ESPN 球队代码
ESPN_TEAMS = {
    "lal": "洛杉矶湖人",
    "bos": "波士顿凯尔特人",
    "gsw": "金州勇士",
    "mil": "密尔沃基雄鹿",
    "phi": "费城76人",
    "cle": "克利夫兰骑士",
    "mia": "迈阿密热火",
    "ny": "纽约尼克斯",
    "bkn": "布鲁克林篮网",
    "tor": "多伦多猛龙",
    "chi": "芝加哥公牛",
    "det": "底特律活塞",
    "ind": "印第安纳步行者",
    "atl": "亚特兰大老鹰",
    "cha": "夏洛特黄蜂",
    "orl": "奥兰多魔术",
    "wsh": "华盛顿奇才",
    "okc": "俄克拉荷马城雷霆",
    "den": "丹佛掘金",
    "min": "明尼苏达森林狼",
    "por": "波特兰开拓者",
    "utah": "犹他爵士",
    "lac": "洛杉矶快船",
    "phx": "菲尼克斯太阳",
    "sac": "萨克拉门托国王",
    "dal": "达拉斯独行侠",
    "hou": "休斯顿火箭",
    "mem": "孟菲斯灰熊",
    "no": "新奥尔良鹈鹕",
    "sa": "圣安东尼奥马刺",
}


class ESPNSpider:
    """ESPN NBA 数据爬虫"""
    
    def __init__(self):
        self.roster_parser = ESPNRosterParser()
        self.stats_parser = ESPNStatsParser()
        self.standings_parser = ESPNStandingsParser()
        self.team_stats_parser = ESPNTeamStatsParser()
        self.storage = CSVStorage()

    
    def crawl_roster(self, team_code, season="2024-25"):
        """
        爬取单个球队的名单（含薪资）
        
        Args:
            team_code: ESPN 球队代码
            season: 赛季
        """
        team_name = ESPN_TEAMS.get(team_code, team_code)
        print(f"\n开始爬取 ESPN {team_name} 球员名单")
        
        url = self.roster_parser.get_roster_url(team_code)
        html = get_page(url)
        
        if not html:
            print(f"[失败] 无法获取数据")
            return []
        
        data = self.roster_parser.parse(html, team_name)
        
        if not data:
            print(f"[警告] 未解析到数据")
            return []
        
        # 添加赛季信息
        for item in data:
            item["赛季"] = season
        
        print(f"[完成] 共爬取 {len(data)} 名球员")
        return data
    
    def crawl_all_rosters(self, season="2024-25"):
        """
        爬取所有球队的名单
        
        Args:
            season: 赛季
        """
        print(f"\n{'='*60}")
        print(f"开始从 ESPN 爬取所有球队球员名单 - {season}赛季")
        print(f"{'='*60}")
        
        all_data = []
        
        for team_code, team_name in ESPN_TEAMS.items():
            data = self.crawl_roster(team_code, season)
            all_data.extend(data)
            
            # 保存单个球队数据
            if data:
                filename = f"ESPN_{team_name}_{season}.csv"
                filepath = os.path.join(OUTPUT_SUBDIRS["rosters"], filename)
                import pandas as pd
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False, encoding="utf-8-sig")
                print(f"[保存] {filepath}")
        
        return all_data
    
    def crawl_stats(self, category="points", season="2024-25"):
        """
        爬取球员统计数据
        
        Args:
            category: 统计类别
            season: 赛季
        """
        print(f"\n开始从 ESPN 爬取球员{category}数据")
        
        url = self.stats_parser.STAT_URLS.get(category)
        if not url:
            print(f"[错误] 未知的统计类别: {category}")
            return []
        
        html = get_page(url)
        if not html:
            print(f"[失败] 无法获取数据")
            return []
        
        data = self.stats_parser.parse(html, category)
        
        if data:
            for item in data:
                item["赛季"] = season
            print(f"[完成] 共爬取 {len(data)} 条记录")
        
        return data
    
    def crawl_standings(self, season="2024-25"):
        """
        爬取战绩排行
        
        Args:
            season: 赛季
        """
        print(f"\n开始从 ESPN 爬取战绩排行")
        
        html = get_page(self.standings_parser.base_url)
        if not html:
            print(f"[失败] 无法获取数据")
            return []
        
        data = self.standings_parser.parse(html)
        
        if data:
            for item in data:
                item["赛季"] = season
            print(f"[完成] 共爬取 {len(data)} 支球队")
        
        return data
    
    def crawl_team_stats(self, season="2024-25"):
        """
        爬取球队统计数据
        
        Args:
            season: 赛季
            
        Returns:
            list: 球队统计数据
        """
        print(f"\n{'='*60}")
        print(f"开始从 ESPN 爬取球队统计数据 - {season}赛季")
        print(f"{'='*60}")
        
        # 获取三个视图的数据
        general_url = self.team_stats_parser.get_url("general")
        offensive_url = self.team_stats_parser.get_url("offensive")
        defensive_url = self.team_stats_parser.get_url("defensive")
        
        print(f"[请求] 综合统计: {general_url}")
        general_html = get_page(general_url)
        
        print(f"[请求] 进攻统计: {offensive_url}")
        offensive_html = get_page(offensive_url)
        
        print(f"[请求] 防守统计: {defensive_url}")
        defensive_html = get_page(defensive_url)
        
        if not general_html:
            print("[失败] 无法获取综合统计数据")
            return []
        
        # 合并所有视图的数据
        data = self.team_stats_parser.parse_all_views(
            general_html, 
            offensive_html if offensive_html else "", 
            defensive_html if defensive_html else ""
        )
        
        if data:
            for item in data:
                item["赛季"] = season
            print(f"[完成] 共爬取 {len(data)} 支球队数据")
            
            # 保存数据
            filename = f"ESPN_球队统计_{season}.csv"
            filepath = os.path.join(OUTPUT_SUBDIRS["team_stats"], filename)
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
            print(f"[保存] {filepath}")
        else:
            print("[警告] 未解析到数据")
        
        return data


def test_espn():
    """测试 ESPN 爬虫"""
    spider = ESPNSpider()
    
    # 测试爬取湖人队
    data = spider.crawl_roster("lal")
    
    if data:
        print("\n球员数据示例:")
        for player in data[:5]:
            print(f"  {player.get('Name', '')} - {player.get('POS', '')} - {player.get('Salary', 'N/A')}")


if __name__ == "__main__":
    test_espn()
