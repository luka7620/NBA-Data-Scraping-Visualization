# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - NBA API 模块（使用 nba_api 库）
从 NBA.com 获取详细球员统计数据
"""

import os
import sys
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, playercareerstats
from nba_api.stats.static import players, teams

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR


# 创建输出目录
NBA_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "NBA官方统计")
if not os.path.exists(NBA_OUTPUT_DIR):
    os.makedirs(NBA_OUTPUT_DIR)


class NBAStatsSpider:
    """NBA.com 统计数据爬虫（使用 nba_api 库）"""
    
    def __init__(self):
        pass
    
    def crawl_player_stats(self, season="2024-25", measure_type="Base", per_mode="PerGame"):
        """
        爬取球员统计数据
        
        Args:
            season: 赛季 (格式: 2024-25)
            measure_type: 统计类型 (Base/Advanced/Misc/Four Factors/Scoring/Opponent/Defense)
            per_mode: 统计模式 (PerGame/Totals/Per36)
            
        Returns:
            pd.DataFrame: 球员统计数据
        """
        print(f"\n{'='*60}")
        print(f"从 NBA.com API 爬取球员统计 - {season}赛季")
        print(f"类型: {measure_type} | 模式: {per_mode}")
        print(f"{'='*60}")
        
        try:
            # 使用 nba_api 获取数据
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star="Regular Season",
                measure_type_detailed_defense=measure_type,
                per_mode_detailed=per_mode
            )
            
            df = stats.get_data_frames()[0]
            
            print(f"[完成] 共获取 {len(df)} 名球员数据")
            print(f"[字段] 共 {len(df.columns)} 个字段")
            
            return df
            
        except Exception as e:
            print(f"[错误] {e}")
            return pd.DataFrame()
    
    def crawl_complete_stats(self, season="2024-25", save=True):
        """
        爬取完整统计数据（基础 + 高级）
        
        Args:
            season: 赛季
            save: 是否保存
            
        Returns:
            pd.DataFrame: 完整数据
        """
        print(f"\n{'#'*60}")
        print(f"# 从 NBA.com API 爬取完整球员统计")
        print(f"# 赛季: {season}")
        print(f"{'#'*60}")
        
        # 1. 基础统计 (Per Game)
        base_df = self.crawl_player_stats(season, "Base", "PerGame")
        
        if base_df.empty:
            print("\n[失败] 未获取到基础数据")
            return pd.DataFrame()
        
        # 2. 高级统计
        print("\n")
        adv_df = self.crawl_player_stats(season, "Advanced", "PerGame")
        
        # 合并数据
        if not adv_df.empty and 'PLAYER_ID' in base_df.columns and 'PLAYER_ID' in adv_df.columns:
            # 选择高级统计中的独有字段（排除基础统计中已有的）
            common_cols = set(base_df.columns) & set(adv_df.columns)
            adv_only_cols = [col for col in adv_df.columns if col not in common_cols or col == 'PLAYER_ID']
            
            if len(adv_only_cols) > 1:  # 除了PLAYER_ID还有其他字段
                adv_subset = adv_df[adv_only_cols]
                
                # 合并
                df = base_df.merge(adv_subset, on='PLAYER_ID', how='left')
                print(f"\n[合并] 基础统计 + 高级统计，共 {len(df.columns)} 个字段")
            else:
                df = base_df
                print(f"\n[提示] 高级统计无新增字段，使用基础统计")
        else:
            df = base_df
        
        # 添加赛季信息
        df['赛季'] = season
        
        # 显示数据示例
        print(f"\n{'='*60}")
        print("数据示例（前5名球员）：")
        print(f"{'='*60}")
        
        display_cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'PTS', 'REB', 'AST']
        available_cols = [c for c in display_cols if c in df.columns]
        if available_cols:
            print(df[available_cols].head(5).to_string(index=False))
        
        # 保存文件
        if save:
            filename = f"NBA_完整统计_{season}.csv"
            filepath = os.path.join(NBA_OUTPUT_DIR, filename)
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
            print(f"\n[保存] {filepath}")
            print(f"[数据] {len(df)} 名球员 × {len(df.columns)} 个字段")
        
        return df
    
    def get_all_players(self):
        """获取所有球员列表"""
        return players.get_players()
    
    def get_all_teams(self):
        """获取所有球队列表"""
        return teams.get_teams()


def main():
    """主函数"""
    import argparse
    from config import SEASONS
    
    parser = argparse.ArgumentParser(description="NBA 官方 API 数据爬虫")
    parser.add_argument(
        "--season",
        default="2024-25",
        help="赛季 (默认: 2024-25)"
    )
    parser.add_argument(
        "--all-seasons",
        action="store_true",
        help="爬取最近5年所有赛季数据"
    )
    
    args = parser.parse_args()
    
    spider = NBAStatsSpider()
    
    # 确定要爬取的赛季列表
    seasons_to_crawl = SEASONS if args.all_seasons else [args.season]
    
    print(f"\n{'#'*60}")
    print(f"# NBA 官方 API 数据爬虫")
    print(f"# 目标赛季: {', '.join(seasons_to_crawl)}")
    print(f"{'#'*60}\n")
    
    for season in seasons_to_crawl:
        # 爬取完整统计
        df = spider.crawl_complete_stats(season, save=True)
        
        if not df.empty and season == seasons_to_crawl[0]:
            print(f"\n{'='*60}")
            print("关键统计字段说明：")
            print(f"{'='*60}")
            
            field_desc = {
                "GP": "出场次数",
                "MIN": "场均时间",
                "PTS": "场均得分",
                "REB": "场均篮板",
                "AST": "场均助攻",
                "FG_PCT": "投篮命中率",
                "FG3_PCT": "三分命中率",
                "FT_PCT": "罚球命中率",
                "STL": "场均抢断",
                "BLK": "场均盖帽",
                "TOV": "场均失误",
            }
            
            for field, desc in field_desc.items():
                if field in df.columns:
                    print(f"  {field:12s} - {desc}")


if __name__ == "__main__":
    main()
