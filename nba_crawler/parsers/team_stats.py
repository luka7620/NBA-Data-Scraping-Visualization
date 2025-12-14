# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 球队统计数据解析器
解析球队数据排行页面
"""

from bs4 import BeautifulSoup


class TeamStatsParser:
    """球队统计数据解析器"""
    
    def __init__(self):
        self.default_fields = [
            "排名", "球队", "投篮", "三分", "罚球", 
            "篮板", "助攻", "失误", "抢断", "盖帽", "犯规", "得分"
        ]
    
    def parse(self, html):
        """
        解析球队统计页面
        
        Args:
            html: HTML 内容
            
        Returns:
            list: 球队数据列表
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        data = []
        
        # 查找数据表格
        table = soup.find("table", class_="players_table")
        if not table:
            table = soup.find("table")
        
        if not table:
            print("[警告] 未找到球队统计表格")
            return []
        
        # 解析表头
        headers = []
        thead = table.find("thead")
        if thead:
            for th in thead.find_all("th"):
                headers.append(th.get_text(strip=True))
        
        if not headers:
            headers = self.default_fields
        
        # 解析数据行
        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
        
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            
            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    text = cell.get_text(strip=True)
                    
                    # 提取球队链接
                    link = cell.find("a")
                    if link and link.get("href") and headers[i] == "球队":
                        row_data["球队链接"] = link.get("href")
                    
                    row_data[headers[i]] = text
            
            if row_data:
                data.append(row_data)
        
        return data
