# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 数据清洗模块
处理和标准化爬取的数据
"""

import re
import pandas as pd


class DataCleaner:
    """数据清洗器"""
    
    def __init__(self):
        pass
    
    def clean_player_stats(self, data, category="pts"):
        """
        清洗球员统计数据
        
        Args:
            data: 原始数据列表
            category: 统计类别
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # 移除空行
        df = df.dropna(how="all")
        
        # 数据类型转换
        numeric_columns = {
            "pts": ["场次", "时间", "得分"],
            "reb": ["场次", "前场", "后场", "总篮板"],
            "asts": ["场次", "时间", "助攻"],
            "fgp": ["场次", "命中", "出手"],
            "tpp": ["场次", "命中", "出手"],
            "ftp": ["场次", "命中", "出手"],
            "blk": ["场次", "时间", "盖帽"],
            "stl": ["场次", "时间", "抢断"],
        }
        
        cols_to_convert = numeric_columns.get(category, [])
        for col in cols_to_convert:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # 处理命中率列（去除百分号）
        if "命中率" in df.columns:
            df["命中率"] = df["命中率"].apply(self._parse_percentage)
        
        # 处理排名（确保为整数）
        if "排名" in df.columns:
            df["排名"] = pd.to_numeric(df["排名"], errors="coerce").astype("Int64")
        
        # 去除重复行
        df = df.drop_duplicates()
        
        return df
    
    def clean_team_stats(self, data):
        """
        清洗球队统计数据
        
        Args:
            data: 原始数据列表
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.dropna(how="all")
        
        # 数值列转换
        numeric_cols = ["投篮", "三分", "罚球", "篮板", "助攻", "失误", "抢断", "盖帽", "犯规", "得分"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        if "排名" in df.columns:
            df["排名"] = pd.to_numeric(df["排名"], errors="coerce").astype("Int64")
        
        df = df.drop_duplicates()
        return df
    
    def clean_standings(self, data):
        """
        清洗战绩排行数据
        
        Args:
            data: 原始数据列表
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.dropna(how="all")
        
        # 数值列转换
        if "胜" in df.columns:
            df["胜"] = pd.to_numeric(df["胜"], errors="coerce").astype("Int64")
        if "负" in df.columns:
            df["负"] = pd.to_numeric(df["负"], errors="coerce").astype("Int64")
        if "排名" in df.columns:
            df["排名"] = pd.to_numeric(df["排名"], errors="coerce").astype("Int64")
        
        # 处理胜率
        if "胜率" in df.columns:
            df["胜率"] = df["胜率"].apply(self._parse_percentage)
        
        df = df.drop_duplicates()
        return df
    
    def clean_roster(self, data):
        """
        清洗球员名单数据
        
        Args:
            data: 原始数据列表
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.dropna(how="all")
        
        # 文本清洗
        if "球员" in df.columns:
            df["球员"] = df["球员"].str.strip()
        if "英文名" in df.columns:
            df["英文名"] = df["英文名"].str.strip()
        
        df = df.drop_duplicates(subset=["球员"])
        return df
    
    def _parse_percentage(self, value):
        """
        解析百分比字符串
        
        Args:
            value: 百分比字符串（如 "45.6%" 或 ".456"）
            
        Returns:
            float: 百分比数值
        """
        if pd.isna(value):
            return None
        
        value = str(value).strip()
        
        # 处理百分号
        if "%" in value:
            value = value.replace("%", "")
            try:
                return float(value)
            except ValueError:
                return None
        
        # 处理小数形式
        try:
            num = float(value)
            if num <= 1:
                return num * 100
            return num
        except ValueError:
            return None


# 创建全局清洗器实例
data_cleaner = DataCleaner()
