# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 主控制程序
整合各模块，执行数据采集任务
"""

import argparse
import sys
from config import SEASONS, PLAYER_STATS_CATEGORIES, TEAMS, URLS, BASE_URL
from request_handler import get_page
from parsers import PlayerStatsParser, TeamStatsParser, StandingsParser, RosterParser
from data_cleaner import data_cleaner
from storage import csv_storage


class NBASpider:
    """NBA 数据爬虫主类"""
    
    def __init__(self):
        self.player_parser = PlayerStatsParser()
        self.team_parser = TeamStatsParser()
        self.standings_parser = StandingsParser()
        self.roster_parser = RosterParser()
    
    def crawl_player_stats(self, category="pts", season="2024-25"):
        """
        爬取球员统计数据
        
        Args:
            category: 统计类别代码
            season: 赛季
        """
        print(f"\n{'='*60}")
        print(f"开始爬取球员{category}数据 - {season}赛季")
        print(f"{'='*60}")
        
        # 构建 URL
        url = BASE_URL + URLS["player_stats"].format(category=category)
        
        # 获取第一页
        html = get_page(url)
        if not html:
            print(f"[失败] 无法获取数据")
            return
        
        # 解析数据
        data = self.player_parser.parse(html, category)
        
        if not data:
            print(f"[警告] 未解析到数据")
            return
        
        # 清洗数据
        df = data_cleaner.clean_player_stats(data, category)
        
        # 添加赛季信息
        df["赛季"] = season
        
        # 保存数据
        csv_storage.save_player_stats(df, category, season)
        
        print(f"[完成] 共爬取 {len(df)} 条记录")
    
    def crawl_team_stats(self, season="2024-25"):
        """
        爬取球队统计数据(尝试多数据源)
        
        Args:
            season: 赛季
        """
        print(f"\n{'='*60}")
        print(f"开始爬取球队统计数据 - {season}赛季")
        print(f"{'='*60}")
        
        # 主要数据源: 虎扑
        print(f"\n[数据源] 虎扑 NBA")
        url = BASE_URL + URLS["team_stats"]
        html = get_page(url)
        
        if not html:
            print(f"[失败] 无法获取数据")
            return
        
        data = self.team_parser.parse(html)
        
        if not data:
            print(f"[警告] 未解析到数据")
            return
        
        df = data_cleaner.clean_team_stats(data)
        df["赛季"] = season
        
        csv_storage.save_team_stats(df, season)
        print(f"[完成] 共爬取 {len(df)} 条记录")
        
        # 尝试从ESPN获取额外数据(可选)
        try:
            print(f"\n[可选] 尝试从 ESPN 获取额外球队数据...")
            from espn_crawler import ESPNSpider
            espn_spider = ESPNSpider()
            espn_data = espn_spider.crawl_team_stats(season)
            if espn_data:
                print(f"[成功] ESPN 数据已保存")
        except Exception as e:
            print(f"[跳过] ESPN 数据获取失败: {e}")

    
    def crawl_standings(self, season="2024-25"):
        """
        爬取战绩排行数据
        
        Args:
            season: 赛季
        """
        print(f"\n{'='*60}")
        print(f"开始爬取战绩排行 - {season}赛季")
        print(f"{'='*60}")
        
        url = BASE_URL + URLS["standings"]
        html = get_page(url)
        
        if not html:
            print(f"[失败] 无法获取数据")
            return
        
        data = self.standings_parser.parse_to_list(html)
        
        if not data:
            print(f"[警告] 未解析到数据")
            return
        
        df = data_cleaner.clean_standings(data)
        df["赛季"] = season
        
        csv_storage.save_standings(df, season)
        print(f"[完成] 共爬取 {len(df)} 条记录")
    
    def crawl_roster(self, team_code, season="2024-25"):
        """
        爬取球队球员名单
        
        Args:
            team_code: 球队代码
            season: 赛季
        """
        team_name = TEAMS.get(team_code, team_code)
        print(f"\n开始爬取 {team_name} 球员名单 - {season}赛季")
        
        url = BASE_URL + URLS["roster"].format(team_code=team_code)
        html = get_page(url)
        
        if not html:
            print(f"[失败] 无法获取数据")
            return
        
        data = self.roster_parser.parse(html, team_name)
        
        if not data:
            print(f"[警告] 未解析到数据")
            return
        
        df = data_cleaner.clean_roster(data)
        df["赛季"] = season
        
        csv_storage.save_roster(df, team_code, season)
        print(f"[完成] 共爬取 {len(df)} 条记录")
    
    def crawl_all_rosters(self, season="2024-25"):
        """
        爬取所有球队的球员名单
        
        Args:
            season: 赛季
        """
        print(f"\n{'='*60}")
        print(f"开始爬取所有球队球员名单 - {season}赛季")
        print(f"{'='*60}")
        
        for team_code in TEAMS.keys():
            self.crawl_roster(team_code, season)
    
    def crawl_priority_stats(self, season="2024-25"):
        """
        爬取优先级数据（按新的顺序：先球队名单，再得分/篮板/助攻）
        
        Args:
            season: 赛季
        """
        print(f"\n{'='*60}")
        print(f"开始爬取优先级数据 - {season}赛季")
        print(f"{'='*60}")
        
        # 第一步：爬取所有球队的现役球员名单
        print(f"\n{'#'*60}")
        print(f"# 第一步：爬取30支球队的现役球员名单")
        print(f"{'#'*60}\n")
        self.crawl_all_rosters(season)
        
        # 第二步：分别爬取得分榜、助攻榜、篮板榜
        print(f"\n{'#'*60}")
        print(f"# 第二步：爬取球员统计数据（得分/篮板/助攻）")
        print(f"{'#'*60}\n")
        
        priority_categories = [
            {"name": "得分榜", "code": "pts"},
            {"name": "篮板榜", "code": "reb"},
            {"name": "助攻榜", "code": "asts"},
        ]
        
        for cat in priority_categories:
            print(f"\n--- {cat['name']} ---")
            self.crawl_player_stats(cat["code"], season)
        
        # 第三步：爬取战绩排行
        print(f"\n{'#'*60}")
        print(f"# 第三步：爬取战绩排行榜")
        print(f"{'#'*60}\n")
        self.crawl_standings(season)
    
    def crawl_all_player_stats(self, season="2024-25"):
        """
        爬取所有球员统计数据
        
        Args:
            season: 赛季
        """
        for cat in PLAYER_STATS_CATEGORIES:
            self.crawl_player_stats(cat["code"], season)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NBA 篮球数据爬虫")
    parser.add_argument(
        "--type",
        choices=["player", "team", "standings", "roster", "priority", "all"],
        default="priority",
        help="爬取数据类型 (默认: priority - 得分/篮板/助攻)"
    )
    parser.add_argument(
        "--season",
        default="2024-25",
        help="赛季 (默认: 2024-25)"
    )
    parser.add_argument(
        "--category",
        default="pts",
        help="球员统计类别 (pts/reb/asts等，仅当 type=player 时有效)"
    )
    parser.add_argument(
        "--all-seasons",
        action="store_true",
        help="爬取最近5年所有赛季数据"
    )
    
    args = parser.parse_args()
    
    spider = NBASpider()
    
    # 确定要爬取的赛季列表
    seasons = SEASONS if args.all_seasons else [args.season]
    
    print(f"\n{'#'*60}")
    print(f"# NBA 篮球数据爬虫系统")
    print(f"# 数据来源: 虎扑 NBA")
    print(f"# 赛季: {', '.join(seasons)}")
    print(f"{'#'*60}\n")
    
    try:
        for season in seasons:
            if args.type == "player":
                spider.crawl_player_stats(args.category, season)
            elif args.type == "team":
                spider.crawl_team_stats(season)
            elif args.type == "standings":
                spider.crawl_standings(season)
            elif args.type == "roster":
                spider.crawl_all_rosters(season)
            elif args.type == "priority":
                # 优先级数据：得分、篮板、助攻
                spider.crawl_priority_stats(season)
                spider.crawl_standings(season)
            elif args.type == "all":
                # 所有数据
                spider.crawl_all_player_stats(season)
                spider.crawl_team_stats(season)
                spider.crawl_standings(season)
                spider.crawl_all_rosters(season)
        
        print(f"\n{'='*60}")
        print(f"爬取任务完成！")
        print(f"输出文件位置: {csv_storage.output_dir}")
        print(f"{'='*60}\n")
        
        # 显示生成的文件
        files = csv_storage.get_output_files()
        if files:
            print("生成的文件:")
            for f in files:
                print(f"  - {f}")
        
    except KeyboardInterrupt:
        print("\n\n[中断] 用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
