# -*- coding: utf-8 -*-
"""
ESPN 球员统计解析器
从 ESPN 提取球员统计数据
"""

from bs4 import BeautifulSoup


class ESPNStatsParser:
    """ESPN 球员统计解析器"""
    
    STAT_URLS = {
        "points": "https://www.espn.com/nba/stats/player",
        "assists": "https://www.espn.com/nba/stats/player/_/table/offensive/sort/avgAssists/dir/desc",
        "rebounds": "https://www.espn.com/nba/stats/player/_/table/general/sort/avgRebounds/dir/desc",
        "blocks": "https://www.espn.com/nba/stats/player/_/table/defensive/sort/avgBlocks/dir/desc",
        "steals": "https://www.espn.com/nba/stats/player/_/table/defensive/sort/avgSteals/dir/desc",
        "3pm": "https://www.espn.com/nba/stats/player/_/table/offensive/sort/avgThreePointFieldGoalsMade/dir/desc",
    }
    
    def __init__(self):
        pass
    
    def parse(self, html, category="points"):
        """
        解析 ESPN 球员统计页面
        
        Args:
            html: HTML 内容
            category: 统计类别
            
        Returns:
            list: 球员统计数据列表
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        data = []
        
        # ESPN 使用表格展示数据
        tables = soup.find_all("table")
        
        for table in tables:
            # 查找表头
            thead = table.find("thead")
            if not thead:
                continue
            
            headers = []
            for th in thead.find_all("th"):
                headers.append(th.get_text(strip=True))
            
            # 解析数据
            tbody = table.find("tbody")
            if not tbody:
                continue
            
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if not cells:
                    continue
                
                row_data = {"Category": category}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        text = cell.get_text(strip=True)
                        row_data[headers[i]] = text
                        
                        # 提取球员链接
                        link = cell.find("a")
                        if link and "/nba/player/" in link.get("href", ""):
                            row_data["PlayerLink"] = link.get("href")
                
                if row_data:
                    data.append(row_data)
        
        return data
