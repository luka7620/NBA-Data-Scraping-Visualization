# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 数据存储模块
将数据保存为 CSV 文件
"""

import os
import pandas as pd
from config import OUTPUT_DIR, OUTPUT_SUBDIRS


class CSVStorage:
    """CSV 文件存储器"""
    
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def save(self, data, filename, mode="w"):
        """
        保存数据到 CSV 文件
        
        Args:
            data: DataFrame 或 字典列表
            filename: 文件名（不含路径）
            mode: 写入模式 ('w' 覆盖, 'a' 追加)
            
        Returns:
            str: 保存的文件路径
        """
        # 转换为 DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据格式不支持，需要 DataFrame 或列表")
        
        # 如果数据为空，不保存
        if df.empty:
            print(f"[警告] 数据为空，跳过保存: {filename}")
            return None
        
        # 构建完整路径
        filepath = os.path.join(self.output_dir, filename)
        
        # 保存文件
        try:
            if mode == "a" and os.path.exists(filepath):
                # 追加模式：不写入表头
                df.to_csv(filepath, mode="a", index=False, header=False, encoding="utf-8-sig")
            else:
                # 覆盖模式：写入表头
                df.to_csv(filepath, mode="w", index=False, encoding="utf-8-sig")
            
            print(f"[保存] {filepath} ({len(df)} 条记录)")
            return filepath
        except Exception as e:
            print(f"[错误] 保存文件失败: {e}")
            return None
    
    def save_player_stats(self, data, category, season):
        """
        保存球员统计数据到 球员统计/ 目录
        
        Args:
            data: 数据
            category: 统计类别代码
            season: 赛季
        """
        # 使用中文名称
        category_names = {
            "pts": "得分榜",
            "reb": "篮板榜",
            "asts": "助攻榜",
            "fgp": "投篮命中率",
            "tpp": "三分命中率",
            "ftp": "罚球命中率",
            "blk": "盖帽榜",
            "stl": "抢断榜",
        }
        category_name = category_names.get(category, category)
        filename = f"{category_name}_{season}.csv"
        
        # 保存到球员统计子目录
        filepath = os.path.join(OUTPUT_SUBDIRS["player_stats"], filename)
        
        # 转换为 DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据格式不支持，需要 DataFrame 或列表")
        
        if df.empty:
            print(f"[警告] 数据为空，跳过保存: {filename}")
            return None
        
        try:
            df.to_csv(filepath, mode="w", index=False, encoding="utf-8-sig")
            print(f"[保存] {filepath} ({len(df)} 条记录)")
            return filepath
        except Exception as e:
            print(f"[错误] 保存文件失败: {e}")
            return None
    
    def save_team_stats(self, data, season):
        """
        保存球队统计数据到 球队统计/ 目录
        
        Args:
            data: 数据
            season: 赛季
        """
        filename = f"球队数据_{season}.csv"
        filepath = os.path.join(OUTPUT_SUBDIRS["team_stats"], filename)
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据格式不支持")
        
        if df.empty:
            print(f"[警告] 数据为空，跳过保存: {filename}")
            return None
        
        try:
            df.to_csv(filepath, mode="w", index=False, encoding="utf-8-sig")
            print(f"[保存] {filepath} ({len(df)} 条记录)")
            return filepath
        except Exception as e:
            print(f"[错误] 保存文件失败: {e}")
            return None
    
    def save_standings(self, data, season):
        """
        保存战绩排行数据到 战绩排行/ 目录
        
        Args:
            data: 数据
            season: 赛季
        """
        filename = f"战绩排行_{season}.csv"
        filepath = os.path.join(OUTPUT_SUBDIRS["standings"], filename)
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据格式不支持")
        
        if df.empty:
            print(f"[警告] 数据为空，跳过保存: {filename}")
            return None
        
        try:
            df.to_csv(filepath, mode="w", index=False, encoding="utf-8-sig")
            print(f"[保存] {filepath} ({len(df)} 条记录)")
            return filepath
        except Exception as e:
            print(f"[错误] 保存文件失败: {e}")
            return None
    
    def save_roster(self, data, team_code, season):
        """
        保存球队球员名单到 球队名单/ 目录
        
        Args:
            data: 数据
            team_code: 球队代码
            season: 赛季
        """
        from config import TEAMS
        team_name = TEAMS.get(team_code, team_code)
        filename = f"{team_name}_{season}.csv"
        filepath = os.path.join(OUTPUT_SUBDIRS["rosters"], filename)
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("数据格式不支持")
        
        if df.empty:
            print(f"[警告] 数据为空，跳过保存: {filename}")
            return None
        
        try:
            df.to_csv(filepath, mode="w", index=False, encoding="utf-8-sig")
            print(f"[保存] {filepath} ({len(df)} 条记录)")
            return filepath
        except Exception as e:
            print(f"[错误] 保存文件失败: {e}")
            return None
    
    def get_output_files(self):
        """
        获取所有已生成的输出文件列表
        
        Returns:
            list: 文件路径列表
        """
        if not os.path.exists(self.output_dir):
            return []
        
        files = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith(".csv"):
                files.append(os.path.join(self.output_dir, filename))
        return files


# 创建全局存储器实例
csv_storage = CSVStorage()
