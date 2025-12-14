# -*- coding: utf-8 -*-
"""
ESPN 战绩排行解析器
从 ESPN 提取 NBA 战绩排行
"""

from bs4 import BeautifulSoup


class ESPNStandingsParser:
    """ESPN 战绩排行解析器"""
    
    def __init__(self):
        self.base_url = "https://www.espn.com/nba/standings"
    
    def parse(self, html):
        """
        解析 ESPN 战绩排行页面
        
        Args:
            html: HTML 内容
            
        Returns:
            list: 战绩数据列表
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        data = []
        
        # ESPN 使用表格展示战绩
        tables = soup.find_all("table")
        
        for table in tables:
            # 查找表头
            thead = table.find("thead")
            if not thead:
                continue
            
            headers = []
            for th in thead.find_all("th"):
                headers.append(th.get_text(strip=True))
            
            # 检查是否包含战绩数据
            if not any(h in headers for h in ["W", "L", "PCT"]):
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
                
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        text = cell.get_text(strip=True)
                        row_data[headers[i]] = text
                        
                        # 提取球队链接
                        link = cell.find("a")
                        if link and "/nba/team/" in link.get("href", ""):
                            row_data["TeamLink"] = link.get("href")
                
                if row_data:
                    data.append(row_data)
        
        return data
