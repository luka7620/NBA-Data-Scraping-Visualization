# -*- coding: utf-8 -*-
"""
NBA 篮球数据爬虫 - 数据整合模块
将虎扑和ESPN数据合并，补充薪资信息
"""

import os
import re
import pandas as pd
from config import OUTPUT_SUBDIRS, TEAMS


# 虎扑球队名 -> ESPN球队代码映射
HUPU_TO_ESPN = {
    "波士顿凯尔特人": "bos",
    "布鲁克林篮网": "bkn",
    "纽约尼克斯": "ny",
    "费城76人": "phi",
    "多伦多猛龙": "tor",
    "芝加哥公牛": "chi",
    "克利夫兰骑士": "cle",
    "底特律活塞": "det",
    "印第安纳步行者": "ind",
    "密尔沃基雄鹿": "mil",
    "亚特兰大老鹰": "atl",
    "夏洛特黄蜂": "cha",
    "迈阿密热火": "mia",
    "奥兰多魔术": "orl",
    "华盛顿奇才": "wsh",
    "丹佛掘金": "den",
    "明尼苏达森林狼": "min",
    "俄克拉荷马城雷霆": "okc",
    "波特兰开拓者": "por",
    "犹他爵士": "utah",
    "金州勇士": "gsw",
    "洛杉矶快船": "lac",
    "洛杉矶湖人": "lal",
    "菲尼克斯太阳": "phx",
    "萨克拉门托国王": "sac",
    "达拉斯独行侠": "dal",
    "休斯顿火箭": "hou",
    "孟菲斯灰熊": "mem",
    "新奥尔良鹈鹕": "no",
    "圣安东尼奥马刺": "sa",
}


def normalize_name(name):
    """
    标准化球员姓名用于匹配
    移除特殊字符，转小写
    """
    if not name:
        return ""
    # 移除数字（如号码）
    name = re.sub(r'\d+', '', str(name))
    # 转小写
    name = name.lower()
    # 移除特殊字符，只保留字母和空格
    name = re.sub(r'[^a-z\s]', '', name)
    # 压缩空格
    name = ' '.join(name.split())
    return name


def merge_roster_with_salary(hupu_df, espn_df):
    """
    合并虎扑名单和ESPN薪资数据
    
    Args:
        hupu_df: 虎扑数据 DataFrame
        espn_df: ESPN数据 DataFrame
        
    Returns:
        pd.DataFrame: 合并后的数据
    """
    # 创建匹配用的标准化名称列
    if "英文名" in hupu_df.columns:
        hupu_df["_match_name"] = hupu_df["英文名"].apply(normalize_name)
    else:
        return hupu_df
    
    if "Name" in espn_df.columns:
        espn_df["_match_name"] = espn_df["Name"].apply(normalize_name)
    else:
        return hupu_df
    
    # 准备ESPN薪资数据
    salary_map = {}
    for _, row in espn_df.iterrows():
        match_name = row.get("_match_name", "")
        salary = row.get("Salary", "")
        if match_name and salary:
            salary_map[match_name] = salary
    
    # 匹配薪资
    def find_salary(english_name):
        norm_name = normalize_name(english_name)
        
        # 精确匹配
        if norm_name in salary_map:
            return salary_map[norm_name]
        
        # 尝试部分匹配（姓氏匹配）
        for espn_name, salary in salary_map.items():
            # 取姓氏（最后一个单词）
            hupu_last = norm_name.split()[-1] if norm_name.split() else ""
            espn_last = espn_name.split()[-1] if espn_name.split() else ""
            
            if hupu_last and espn_last and hupu_last == espn_last:
                # 再检查名字首字母
                hupu_first = norm_name.split()[0][0] if norm_name.split() else ""
                espn_first = espn_name.split()[0][0] if espn_name.split() else ""
                if hupu_first == espn_first:
                    return salary
        
        return ""
    
    hupu_df["薪资"] = hupu_df["英文名"].apply(find_salary)
    
    # 删除临时列
    hupu_df = hupu_df.drop(columns=["_match_name"], errors="ignore")
    
    return hupu_df


def integrate_team_roster(team_name, season="2024-25"):
    """
    整合单个球队的数据
    
    Args:
        team_name: 虎扑球队中文名
        season: 赛季
        
    Returns:
        pd.DataFrame: 整合后的数据
    """
    from espn_crawler import ESPNSpider
    
    # 获取ESPN球队代码
    espn_code = HUPU_TO_ESPN.get(team_name)
    if not espn_code:
        print(f"[警告] 未找到 {team_name} 的ESPN代码")
        return None
    
    # 读取虎扑数据
    hupu_file = os.path.join(OUTPUT_SUBDIRS["rosters"], f"{team_name}_{season}.csv")
    if not os.path.exists(hupu_file):
        print(f"[警告] 虎扑数据文件不存在: {hupu_file}")
        return None
    
    hupu_df = pd.read_csv(hupu_file)
    print(f"[读取] 虎扑 {team_name}: {len(hupu_df)} 名球员")
    
    # 爬取ESPN数据
    spider = ESPNSpider()
    espn_data = spider.crawl_roster(espn_code, season)
    
    if not espn_data:
        print(f"[警告] ESPN数据为空")
        return hupu_df
    
    espn_df = pd.DataFrame(espn_data)
    print(f"[获取] ESPN {team_name}: {len(espn_df)} 名球员")
    
    # 合并数据
    merged_df = merge_roster_with_salary(hupu_df, espn_df)
    
    # 统计匹配结果
    matched = merged_df["薪资"].notna() & (merged_df["薪资"] != "")
    print(f"[匹配] 成功匹配薪资: {matched.sum()}/{len(merged_df)} 名球员")
    
    return merged_df


def integrate_all_rosters(season="2024-25", save=True):
    """
    整合所有球队的数据
    
    Args:
        season: 赛季
        save: 是否保存文件
    """
    print(f"\n{'='*60}")
    print(f"开始整合虎扑与ESPN数据 - {season}赛季")
    print(f"{'='*60}")
    
    # 创建整合数据目录
    merged_dir = os.path.join(OUTPUT_SUBDIRS["rosters"], "整合数据")
    if not os.path.exists(merged_dir):
        os.makedirs(merged_dir)
    
    total_players = 0
    total_matched = 0
    
    for team_name in HUPU_TO_ESPN.keys():
        print(f"\n--- {team_name} ---")
        
        merged_df = integrate_team_roster(team_name, season)
        
        if merged_df is not None:
            total_players += len(merged_df)
            matched = merged_df["薪资"].notna() & (merged_df["薪资"] != "")
            total_matched += matched.sum()
            
            if save:
                # 保存整合后的数据
                output_file = os.path.join(merged_dir, f"{team_name}_{season}.csv")
                merged_df.to_csv(output_file, index=False, encoding="utf-8-sig")
                print(f"[保存] {output_file}")
    
    print(f"\n{'='*60}")
    print(f"整合完成！")
    print(f"总球员数: {total_players}")
    print(f"薪资匹配成功: {total_matched} ({total_matched/total_players*100:.1f}%)")
    print(f"整合数据保存在: {merged_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # 测试单个球队
    # integrate_team_roster("洛杉矶湖人")
    
    # 整合所有球队
    integrate_all_rosters()
