# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 战绩排行解析器
解析 NBA 战绩排行榜页面
"""

from bs4 import BeautifulSoup


class StandingsParser:
    """战绩排行解析器"""
    
    def __init__(self):
        self.default_fields = [
            "排名", "球队", "胜", "负", "胜率", "胜差",
            "主场", "客场", "分区", "最近10场", "连胜/连负"
        ]
        
        # 东部球队列表（用于识别联盟）
        self.eastern_teams = [
            "活塞", "尼克斯", "凯尔特人", "魔术", "76人", "猛龙", "骑士",
            "热火", "老鹰", "雄鹿", "公牛", "黄蜂", "篮网", "步行者", "奇才"
        ]
        
        # 西部球队列表
        self.western_teams = [
            "雷霆", "掘金", "火箭", "湖人", "马刺", "森林狼", "太阳",
            "勇士", "灰熊", "独行侠", "爵士", "开拓者", "国王", "快船", "鹈鹕"
        ]
    
    def parse(self, html):
        """
        解析战绩排行页面
        
        Args:
            html: HTML 内容
            
        Returns:
            dict: 包含东西部排行的数据
        """
        if not html:
            return {"eastern": [], "western": []}
        
        soup = BeautifulSoup(html, "lxml")
        result = {
            "eastern": [],  # 东部
            "western": [],  # 西部
        }
        
        # 查找表格
        table = soup.find("table", class_="players_table")
        if not table:
            table = soup.find("table")
        
        if not table:
            return result
        
        # 获取所有行
        rows = table.find_all("tr")
        
        # 当前联盟（通过检测标题行或球队名来判断）
        current_conference = "eastern"  # 默认东部（通常东部在前）
        found_western = False
        
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            
            # 获取行文本用于判断
            row_text = row.get_text()
            
            # 检测是否是联盟标题行
            if "西部" in row_text and not found_western:
                current_conference = "western"
                found_western = True
                continue
            
            # 跳过表头行（包含"队名"等）
            if "队名" in row_text or "胜场差" in row_text:
                continue
            
            # 尝试提取球队名
            team_name = ""
            for cell in cells:
                link = cell.find("a")
                if link:
                    team_name = link.get_text(strip=True)
                    break
            
            # 如果没有找到链接，尝试第二个单元格
            if not team_name and len(cells) > 1:
                team_name = cells[1].get_text(strip=True)
            
            # 根据球队名判断联盟
            if team_name:
                if any(west_team in team_name for west_team in self.western_teams):
                    current_conference = "western"
                elif any(east_team in team_name for east_team in self.eastern_teams):
                    current_conference = "eastern"
            
            # 解析数据行
            row_data = {"联盟": "东部" if current_conference == "eastern" else "西部"}
            
            # 解析各列数据
            col_index = 0
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                
                # 跳过空列
                if not text:
                    continue
                
                # 提取球队链接
                link = cell.find("a")
                if link and link.get("href"):
                    row_data["球队链接"] = link.get("href")
                
                # 根据列索引分配字段
                if col_index < len(self.default_fields):
                    field = self.default_fields[col_index]
                    row_data[field] = text
                
                col_index += 1
            
            # 只添加有效数据行（必须有球队名和胜场数据）
            if row_data.get("球队") and row_data.get("胜"):
                result[current_conference].append(row_data)
        
        return result
    
    def parse_to_list(self, html):
        """
        解析为统一列表格式（合并东西部）
        
        Args:
            html: HTML 内容
            
        Returns:
            list: 所有球队排行数据列表
        """
        data = self.parse(html)
        all_standings = []
        all_standings.extend(data.get("eastern", []))
        all_standings.extend(data.get("western", []))
        return all_standings
