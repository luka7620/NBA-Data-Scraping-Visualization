# -*- coding: utf-8 -*-
"""
ESPN 球队统计解析器
从 ESPN 提取球队统计数据
"""

from bs4 import BeautifulSoup


class ESPNTeamStatsParser:
    """ESPN 球队统计解析器"""
    
    # ESPN 球队统计 URL
    TEAM_STATS_URLS = {
        "general": "https://www.espn.com/nba/stats/team",
        "offensive": "https://www.espn.com/nba/stats/team/_/view/offensive",
        "defensive": "https://www.espn.com/nba/stats/team/_/view/defensive",
    }
    
    def __init__(self):
        pass
    
    def get_url(self, view="general"):
        """
        获取球队统计 URL
        
        Args:
            view: 视图类型 (general/offensive/defensive)
            
        Returns:
            str: URL
        """
        return self.TEAM_STATS_URLS.get(view, self.TEAM_STATS_URLS["general"])
    
    def parse(self, html, view="general"):
        """
        解析 ESPN 球队统计页面
        
        Args:
            html: HTML 内容
            view: 视图类型
            
        Returns:
            list: 球队统计数据列表
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        data = []
        
        # ESPN 使用表格展示数据
        tables = soup.find_all("table", class_="Table")
        
        if not tables:
            # 尝试查找任何表格
            tables = soup.find_all("table")
        
        for table in tables:
            # 查找表头
            thead = table.find("thead")
            if not thead:
                continue
            
            headers = []
            header_rows = thead.find_all("tr")
            
            # ESPN 可能有多行表头,取最后一行
            if header_rows:
                last_header_row = header_rows[-1]
                for th in last_header_row.find_all("th"):
                    header_text = th.get_text(strip=True)
                    # 跳过空表头
                    if header_text:
                        headers.append(header_text)
            
            if not headers:
                continue
            
            # 解析数据
            tbody = table.find("tbody")
            if not tbody:
                continue
            
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if not cells:
                    continue
                
                row_data = {"View": view}
                
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        text = cell.get_text(strip=True)
                        row_data[headers[i]] = text
                        
                        # 提取球队链接
                        link = cell.find("a")
                        if link and "/nba/team/" in link.get("href", ""):
                            row_data["TeamLink"] = link.get("href")
                            # 提取球队代码
                            href = link.get("href", "")
                            if "/_/name/" in href:
                                team_code = href.split("/_/name/")[1].split("/")[0]
                                row_data["TeamCode"] = team_code
                
                if row_data and len(row_data) > 1:  # 至少有View之外的数据
                    data.append(row_data)
        
        return data
    
    def parse_all_views(self, general_html, offensive_html, defensive_html):
        """
        解析所有视图的球队统计数据并合并
        
        Args:
            general_html: 综合统计 HTML
            offensive_html: 进攻统计 HTML
            defensive_html: 防守统计 HTML
            
        Returns:
            list: 合并后的球队统计数据
        """
        # 解析各个视图
        general_data = self.parse(general_html, "general")
        offensive_data = self.parse(offensive_html, "offensive")
        defensive_data = self.parse(defensive_html, "defensive")
        
        # 以球队名称为键进行合并
        merged_data = {}
        
        # 处理综合数据
        for item in general_data:
            team_name = item.get("Team", item.get("NAME", ""))
            if team_name:
                merged_data[team_name] = item.copy()
        
        # 合并进攻数据
        for item in offensive_data:
            team_name = item.get("Team", item.get("NAME", ""))
            if team_name and team_name in merged_data:
                # 添加进攻数据,避免重复字段
                for key, value in item.items():
                    if key not in merged_data[team_name] or key == "View":
                        if key != "View":
                            merged_data[team_name][f"OFF_{key}"] = value
        
        # 合并防守数据
        for item in defensive_data:
            team_name = item.get("Team", item.get("NAME", ""))
            if team_name and team_name in merged_data:
                # 添加防守数据,避免重复字段
                for key, value in item.items():
                    if key not in merged_data[team_name] or key == "View":
                        if key != "View":
                            merged_data[team_name][f"DEF_{key}"] = value
        
        # 转换为列表
        result = list(merged_data.values())
        
        return result
