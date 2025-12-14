# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 球员统计数据解析器
解析得分、篮板、助攻等球员统计页面
"""

from bs4 import BeautifulSoup
import re


class PlayerStatsParser:
    """球员统计数据解析器"""
    
    def __init__(self):
        self.category_fields = {
            "pts": ["排名", "球员", "球队", "场次", "时间", "得分"],
            "reb": ["排名", "球员", "球队", "场次", "前场", "后场", "总篮板"],
            "asts": ["排名", "球员", "球队", "场次", "时间", "助攻"],
            "fgp": ["排名", "球员", "球队", "场次", "命中", "出手", "命中率"],
            "tpp": ["排名", "球员", "球队", "场次", "命中", "出手", "命中率"],
            "ftp": ["排名", "球员", "球队", "场次", "命中", "出手", "命中率"],
            "blk": ["排名", "球员", "球队", "场次", "时间", "盖帽"],
            "stl": ["排名", "球员", "球队", "场次", "时间", "抢断"],
        }
    
    def parse(self, html, category="pts"):
        """
        解析球员统计页面
        
        Args:
            html: HTML 内容
            category: 统计类别代码 (pts/reb/asts等)
            
        Returns:
            list: 球员数据列表，每项为字典
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        data = []
        
        # 查找数据表格
        table = soup.find("table", class_="players_table")
        if not table:
            # 尝试其他可能的表格选择器
            table = soup.find("table")
        
        if not table:
            print(f"[警告] 未找到数据表格")
            return []
        
        # 解析表头
        headers = []
        thead = table.find("thead")
        if thead:
            for th in thead.find_all("th"):
                headers.append(th.get_text(strip=True))
        
        # 如果没有表头，使用预定义的字段
        if not headers:
            headers = self.category_fields.get(category, ["排名", "球员", "球队", "数据"])
        
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
                    # 提取文本内容
                    text = cell.get_text(strip=True)
                    
                    # 提取链接（如球员详情页）
                    link = cell.find("a")
                    if link and link.get("href"):
                        if headers[i] == "球员":
                            row_data["球员链接"] = link.get("href")
                        elif headers[i] == "球队":
                            row_data["球队链接"] = link.get("href")
                    
                    row_data[headers[i]] = text
            
            if row_data:
                data.append(row_data)
        
        return data
    
    def parse_all_pages(self, html_pages, category="pts"):
        """
        解析多个分页的数据
        
        Args:
            html_pages: HTML 页面列表
            category: 统计类别
            
        Returns:
            list: 合并后的数据列表
        """
        all_data = []
        for html in html_pages:
            page_data = self.parse(html, category)
            all_data.extend(page_data)
        return all_data
    
    def get_page_count(self, html):
        """
        获取分页数量
        
        Args:
            html: HTML 内容
            
        Returns:
            int: 页数
        """
        if not html:
            return 1
        
        soup = BeautifulSoup(html, "lxml")
        
        # 查找分页元素
        pagination = soup.find("div", class_="page")
        if not pagination:
            return 1
        
        # 查找页码链接
        page_links = pagination.find_all("a")
        max_page = 1
        
        for link in page_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            # 尝试从链接或文本中提取页码
            if text.isdigit():
                max_page = max(max_page, int(text))
            else:
                match = re.search(r'/(\d+)$', href)
                if match:
                    max_page = max(max_page, int(match.group(1)))
        
        return max_page
