# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 球队球员名单解析器
解析各球队球员阵容页面
"""

import re
from bs4 import BeautifulSoup


class RosterParser:
    """球队球员名单解析器"""
    
    def __init__(self):
        pass
    
    def parse(self, html, team_name=""):
        """
        解析球队球员名单页面
        
        Args:
            html: HTML 内容
            team_name: 球队名称
            
        Returns:
            list: 球员列表
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        data = []
        
        # 查找球员表格 - 使用class选择器
        table = soup.find("table", class_="players_table")
        if not table:
            # 尝试其他选择器
            table = soup.find("table")
        
        if not table:
            # 如果没有表格，尝试直接查找球员链接
            return self._parse_from_links(soup, team_name)
        
        # 获取所有行
        rows = table.find_all("tr")
        if not rows:
            return []
        
        # 第一行通常是表头
        headers = []
        first_row = rows[0]
        header_cells = first_row.find_all(["th", "td"])
        for cell in header_cells:
            headers.append(cell.get_text(strip=True))
        
        # 如果第一行没有有效表头，使用默认
        if not headers or "姓名" not in headers:
            headers = ["", "姓名", "号码", "位置", "身高", "体重", "生日", "合同"]
        
        # 从第二行开始解析数据
        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells:
                continue
            
            row_data = {"球队": team_name}
            
            for i, cell in enumerate(cells):
                if i >= len(headers):
                    break
                
                header = headers[i]
                
                if header == "姓名" or i == 1:  # 姓名列
                    # 提取球员姓名和链接
                    link = cell.find("a")
                    if link:
                        row_data["球员"] = link.get_text(strip=True)
                        row_data["球员链接"] = link.get("href", "")
                    
                    # 提取英文名（在括号中）
                    cell_text = cell.get_text()
                    english_match = re.search(r'\(([^)]+)\)', cell_text)
                    if english_match:
                        row_data["英文名"] = english_match.group(1)
                elif header == "号码" or i == 2:
                    row_data["号码"] = cell.get_text(strip=True)
                elif header == "位置" or i == 3:
                    row_data["位置"] = cell.get_text(strip=True)
                elif header == "身高" or i == 4:
                    row_data["身高"] = cell.get_text(strip=True)
                elif header == "体重" or i == 5:
                    row_data["体重"] = cell.get_text(strip=True)
                elif header == "生日" or i == 6:
                    row_data["生日"] = cell.get_text(strip=True)
                elif header == "合同" or i == 7:
                    row_data["合同"] = cell.get_text(strip=True)
            
            # 只添加有球员名字的行
            if row_data.get("球员"):
                data.append(row_data)
        
        return data
    
    def _parse_from_links(self, soup, team_name):
        """
        从链接中提取球员信息（备用方法）
        """
        data = []
        player_links = soup.find_all("a", href=lambda x: x and "/players/" in x and ".html" in x)
        
        for link in player_links:
            player_name = link.get_text(strip=True)
            href = link.get("href", "")
            
            if player_name and href:
                # 提取英文名（在父元素中查找括号内容）
                parent_text = link.parent.get_text() if link.parent else ""
                english_match = re.search(r'\(([^)]+)\)', parent_text)
                english_name = english_match.group(1) if english_match else ""
                
                data.append({
                    "球队": team_name,
                    "球员": player_name,
                    "英文名": english_name,
                    "球员链接": href,
                })
        
        return data
