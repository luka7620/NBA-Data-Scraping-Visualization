# -*- coding: utf-8 -*-
"""
ESPN 球队名单解析器
从 ESPN 提取球员名单，包含薪资信息
"""

from bs4 import BeautifulSoup
import re


class ESPNRosterParser:
    """ESPN 球队名单解析器"""
    
    # ESPN 球队代码映射
    TEAM_CODES = {
        "lal": "Los Angeles Lakers",
        "bos": "Boston Celtics",
        "gsw": "Golden State Warriors",
        "mil": "Milwaukee Bucks",
        "phi": "Philadelphia 76ers",
        "cle": "Cleveland Cavaliers",
        "mia": "Miami Heat",
        "ny": "New York Knicks",
        "bkn": "Brooklyn Nets",
        "tor": "Toronto Raptors",
        "chi": "Chicago Bulls",
        "det": "Detroit Pistons",
        "ind": "Indiana Pacers",
        "atl": "Atlanta Hawks",
        "cha": "Charlotte Hornets",
        "orl": "Orlando Magic",
        "wsh": "Washington Wizards",
        "okc": "Oklahoma City Thunder",
        "den": "Denver Nuggets",
        "min": "Minnesota Timberwolves",
        "por": "Portland Trail Blazers",
        "utah": "Utah Jazz",
        "lac": "LA Clippers",
        "phx": "Phoenix Suns",
        "sac": "Sacramento Kings",
        "dal": "Dallas Mavericks",
        "hou": "Houston Rockets",
        "mem": "Memphis Grizzlies",
        "no": "New Orleans Pelicans",
        "sa": "San Antonio Spurs",
    }
    
    def __init__(self):
        self.base_url = "https://www.espn.com/nba/team/roster/_/name"
    
    def get_roster_url(self, team_code):
        """获取球队名单URL"""
        team_name = self.TEAM_CODES.get(team_code, "").lower().replace(" ", "-")
        return f"{self.base_url}/{team_code}/{team_name}"
    
    def parse(self, html, team_name=""):
        """
        解析 ESPN 球队名单页面
        
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
        
        # ESPN 使用表格结构展示球员
        tables = soup.find_all("table")
        
        for table in tables:
            # 查找表头
            thead = table.find("thead")
            if not thead:
                continue
            
            headers = []
            for th in thead.find_all("th"):
                header_text = th.get_text(strip=True)
                headers.append(header_text)
            
            # 检查是否包含球员数据
            if not any(h in headers for h in ["Name", "POS", "Salary"]):
                continue
            
            # 解析数据行
            tbody = table.find("tbody")
            if not tbody:
                continue
            
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if not cells:
                    continue
                
                row_data = {"Team": team_name}
                
                for i, cell in enumerate(cells):
                    if i >= len(headers):
                        break
                    
                    header = headers[i]
                    text = cell.get_text(strip=True)
                    
                    # 提取球员链接
                    if header == "Name":
                        link = cell.find("a")
                        if link:
                            row_data["PlayerLink"] = link.get("href", "")
                    
                    row_data[header] = text
                
                if row_data.get("Name"):
                    data.append(row_data)
        
        # 如果表格解析失败，尝试备用方法
        if not data:
            data = self._parse_from_links(soup, team_name)
        
        return data
    
    def _parse_from_links(self, soup, team_name):
        """备用解析方法：从链接提取球员"""
        data = []
        
        # ESPN 球员链接格式: /nba/player/_/id/xxxxx/player-name
        player_links = soup.find_all("a", href=lambda x: x and "/nba/player/_/id/" in x)
        
        seen_players = set()
        for link in player_links:
            player_name = link.get_text(strip=True)
            href = link.get("href", "")
            
            # 避免重复
            if player_name and player_name not in seen_players:
                seen_players.add(player_name)
                data.append({
                    "Team": team_name,
                    "Name": player_name,
                    "PlayerLink": href,
                })
        
        return data
