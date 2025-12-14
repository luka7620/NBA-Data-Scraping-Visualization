# -*- coding: utf-8 -*-
"""
NBA数据整合模块 - 为NBA官方统计添加中文名
将NBA API的英文数据与虎扑的中文名匹配
"""

import os
import pandas as pd
import re
import requests
from datetime import datetime


import unicodedata

def normalize_name(name):
    """标准化球员姓名用于匹配 (处理特殊字符和重音符号)"""
    if not name or pd.isna(name):
        return ""
    
    # 转换为字符串
    name = str(name)
    
    # Unicode 标准化 (NFD) - 将带重音的字符分解为基字符+重音符
    name = unicodedata.normalize('NFD', name)
    
    # 过滤掉非 ASCII 字符 (主要是重音符)
    name = name.encode('ascii', 'ignore').decode('utf-8')
    
    # 转小写
    name = name.lower()
    
    # 只保留字母和空格
    name = re.sub(r'[^a-z\s]', '', name)
    
    # 规范化空格
    name = ' '.join(name.split())
    
    return name


def crawl_hupu_stats_names():
    """
    爬取虎扑数据页面的球员名单 (补充更多球员)
    
    Returns:
        dict: {英文名标准化: (中文名, 原英文名)}
    """
    print(f"\n[补充] 正在爬取虎扑数据页面以获取更多球员名字...")
    name_mapping = {}
    
    # 基础 URL (得分榜)
    base_url = "https://nba.hupu.com/stats/players/pts/{page}"
    
    # 简单的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    import requests
    from lxml import etree
    import time
    
    # 爬取前 10 页 (约 500 名球员)
    for page in range(1, 11):
        try:
            url = base_url.format(page=page)
            print(f"  - 正在爬取第 {page} 页...")
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                html = etree.HTML(resp.text)
                # 虎扑数据页表格行
                rows = html.xpath('//table[@class="players_table"]//tr[position()>1]')
                
                for row in rows:
                    # 获取中文名 (在第二个 td 的 a 标签中)
                    cn_name_node = row.xpath('./td[2]/a/text()')
                    # 获取详情页链接 (可能包含英文名)
                    link_node = row.xpath('./td[2]/a/@href')
                    
                    if cn_name_node and link_node:
                        cn_name = cn_name_node[0]
                        link = link_node[0]
                        
                        # 从链接中提取英文名 (例如: https://nba.hupu.com/players/lebronjames-65.html)
                        # 提取 'lebronjames'
                        match = re.search(r'/players/([a-zA-Z-]+)-\d+\.html', link)
                        if match:
                            eng_name_slug = match.group(1).replace('-', ' ')
                            # 这是一个近似的英文名，可能没有空格，例如 'lebronjames'
                            # 但我们可以用它来匹配标准化后的名字
                            
                            # 注意: 这种方式提取的英文名可能不带空格 (lebronjames)，而 API 数据是 (LeBron James)
                            # 标准化函数 normalize_name 会去除空格，所以 'lebronjames' == 'lebronjames'
                            # 这是一个很好的匹配方式!
                            
                            normalized = normalize_name(eng_name_slug)
                            if normalized:
                                name_mapping[normalized] = (cn_name, eng_name_slug)
            
            time.sleep(0.5)
        except Exception as e:
            print(f"  [错误] 爬取第 {page} 页失败: {e}")
            
    print(f"[完成] 从虎扑数据页额外获取 {len(name_mapping)} 个名字")
    return name_mapping


def fetch_nba_china_names():
    """
    从 NBA 中国官网 API 获取球员名单 (含中英文名)
    遍历最近几个赛季以确保覆盖尽可能多的球员
    """
    print("正在从 NBA 中国官网获取球员名单...")
    name_map = {}
    
    # 遍历最近 5 个赛季
    current_year = datetime.now().year
    seasons = range(current_year, current_year - 6, -1) # e.g., 2024, 2023, 2022, 2021, 2020
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for year in seasons:
        url = f"https://china.nba.cn/stats2/league/playerlist.json?seasonYear={year}"
        try:
            print(f"正在获取 {year}-{year+1} 赛季球员数据: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                players = data.get('payload', {}).get('players', [])
                
                count = 0
                for p in players:
                    profile = p.get('playerProfile', {})
                    name_en = profile.get('displayNameEn')
                    name_cn = profile.get('displayName')
                    
                    if name_en and name_cn:
                        # 归一化英文名用于匹配
                        normalized_en = normalize_name(name_en)
                        if normalized_en:
                            # 存储: {normalized_en: (chinese_name, original_en_name)}
                            # 保持与原有结构一致，方便后续处理
                            name_map[normalized_en] = (name_cn, name_en)
                            count += 1
                print(f"  - 获取到 {count} 名球员数据")
            else:
                print(f"  - 请求失败 (状态码: {response.status_code})")
        except Exception as e:
            print(f"  - 获取失败: {e}")
            
    print(f"总计获取到 {len(name_map)} 个中英文名映射")
    return name_map

def load_player_names_mapping():
    """
    加载球员中英文映射表
    优先使用 NBA 中国官网数据，辅以手动字典
    """
    # 1. 获取 NBA 中国官网数据
    name_map = fetch_nba_china_names()
    
    # 2. 手动字典 (用于修正或补充官网缺失的，特别是2024届新秀)
    manual_dict = {
        "adam flagler": "亚当-弗拉格勒",
        "chris paul": "克里斯-保罗",
        "ben simmons": "本-西蒙斯",
        
        # 2024 Rookies & Missing Players
        "zaccharie risacher": "扎卡里-里萨谢",
        "alex sarr": "亚历克斯-萨尔",
        "reed sheppard": "里德-谢帕德",
        "stephon castle": "斯蒂芬-卡斯尔",
        "ron holland ii": "龙-霍兰",
        "tidjane salaun": "蒂贾尼-萨隆",
        "donovan clingan": "多诺万-克林根",
        "rob dillingham": "罗伯-迪林厄姆",
        "zach edey": "扎克-伊迪",
        "cody williams": "科迪-威廉姆斯",
        "matas buzelis": "马塔斯-布泽利斯",
        "nikola topic": "尼古拉-托皮奇",
        "devin carter": "德文-卡特",
        "bub carrington": "巴布-卡林顿",
        "kel'el ware": "凯尔-韦尔",
        "jared mccain": "贾里德-麦凯恩",
        "dalton knecht": "道尔顿-克内克特",
        "tristan da silva": "特里斯坦-达-席尔瓦",
        "ja'kobe walter": "贾科比-沃尔特",
        "jaylon tyson": "杰伦-泰森",
        "yves missi": "伊夫-米西",
        "johnny furphy": "约翰尼-弗菲",
        "kyshawn george": "凯肖恩-乔治",
        "dillon jones": "狄龙-琼斯",
        "terrence shannon jr.": "特伦斯-香农",
        "ryan dunn": "瑞安-邓恩",
        "isaiah collier": "以赛亚-科利尔",
        "baylor scheierman": "贝勒-谢尔曼",
        "aj johnson": "AJ-约翰逊",
        "bronny james": "布朗尼-詹姆斯",
        "adem bona": "阿德姆-博纳",
        "cam christie": "卡姆-克里斯蒂",
        "antonio reeves": "安东尼奥-里夫斯",
        "kevin mccullar jr.": "凯文-麦卡勒",
        "jamal shead": "贾马尔-希德",
        "kj simpson": "KJ-辛普森",
        "bobbi klintman": "博比-克林特曼",
        "bobi klintman": "博比-克林特曼",
        "cam spencer": "卡姆-斯潘塞",
        "kyle filipowski": "凯尔-菲利波夫斯基",
        "harrison ingram": "哈里森-英格拉姆",
        "osiris eldridges": "奥西里斯-埃尔德里奇",
        "ariel hukporti": "阿里尔-胡克波尔蒂",
        "armel traore": "阿梅尔-特拉奥雷",
        "christian koloko": "克里斯蒂安-科洛科",
        
        # Edge cases & Mismatches
        "brandon boston": "布兰登-波士顿",
        "cui cui": "崔永熙",
        "guerschon yabusele": "盖尔雄-亚布塞莱",
        "d'angelo russell": "丹吉洛-拉塞尔",
        "elfrid payton": "埃尔弗里德-佩顿",
        "cory joseph": "科里-约瑟夫",
        "alex ducas": "亚历克斯-杜卡斯",
        "alex reese": "亚历克斯-里斯",
        "anton watson": "安东-沃森",
        "branden carlson": "布兰登-卡尔森",
        "isaac jones": "艾萨克-琼斯",
        "kj martin": "肯扬-马丁二世",
        "kenny lofton jr.": "肯尼-洛夫顿",
        "kenneth lofton jr.": "肯尼-洛夫顿",
        
        # Previous missing
        "gg jackson": "GG-杰克逊",
        "gg jackson ii": "GG-杰克逊",
        "g.g. jackson": "GG-杰克逊",
        "vince williams jr.": "文斯-威廉姆斯",
        "scotty pippen jr.": "斯科蒂-皮蓬二世",
        "gregory jackson ii": "GG-杰克逊",
        "trayce jackson-davis": "特雷斯-杰克逊-戴维斯",
        "brandin podziemski": "布兰丁-波杰姆斯基",
        "cam whitmore": "卡姆-惠特摩尔",
        "ausar thompson": "奥萨尔-汤普森",
        "amen thompson": "阿门-汤普森",
        "keyonte george": "基扬特-乔治",
        "jordan hawkins": "乔丹-霍金斯",
        "bilal coulibaly": "比拉尔-库利巴利",
        "jarace walker": "贾雷斯-沃克",
        "taylor hendricks": "泰勒-亨德里克斯",
        "anthony black": "安东尼-布莱克",
        "dereck lively ii": "德雷克-莱夫利二世",
        "gradey dick": "格雷迪-迪克",
        "jett howard": "杰特-霍华德",
        "cason wallace": "卡森-华莱士",
        "kobe bufkin": "科比-巴夫金",
        "olivier-maxence prosper": "奥利维耶-马克桑斯-普罗斯珀",
    }
    
    for en, cn in manual_dict.items():
        norm_en = normalize_name(en)
        if norm_en and norm_en not in name_map:
            name_map[norm_en] = (cn, en)
            
    return name_map


def add_chinese_names_to_nba_stats(nba_stats_file, output_file=None):
    """
    为NBA官方统计添加中文名
    
    Args:
        nba_stats_file: NBA统计CSV文件路径
        output_file: 输出文件路径（可选）
    """
    print(f"\n{'='*60}")
    print("为NBA官方统计数据添加中文名")
    print(f"{'='*60}")
    
    # 1. 读取NBA统计数据
    print(f"\n[读取] {nba_stats_file}")
    nba_df = pd.read_csv(nba_stats_file)
    print(f"  共 {len(nba_df)} 名球员")
    
    # 2. 加载中英文名对照 (使用 NBA 中国官网数据)
    name_mapping = load_player_names_mapping()
    
    if not name_mapping:
        print("\n[警告] 未找到虎扑数据，无法匹配中文名")
        return nba_df
    
    # 3. 匹配中文名
    print(f"\n[匹配] 正在匹配中文名...")
    
    chinese_names = []
    matched_count = 0
    
    for _, row in nba_df.iterrows():
        player_name = row.get('PLAYER_NAME', '')
        normalized = normalize_name(player_name)
        
        if normalized in name_mapping:
            chinese_name, _ = name_mapping[normalized]
            chinese_names.append(chinese_name)
            matched_count += 1
        else:
            chinese_names.append('')  # 未匹配到
    
    # 4. 添加中文名列
    nba_df.insert(1, '球员中文名', chinese_names)
    
    print(f"[完成] 成功匹配 {matched_count}/{len(nba_df)} 名球员 ({matched_count/len(nba_df)*100:.1f}%)")
    
    # 5. 保存文件
    if output_file is None:
        output_file = nba_stats_file.replace('.csv', '_含中文名.csv')
    
    nba_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n[保存] {output_file}")
    
    # 6. 显示示例
    print(f"\n{'='*60}")
    print("数据示例（前10名球员）:")
    print(f"{'='*60}")
    
    display_cols = ['球员中文名', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GP', 'MIN', 'PTS', 'REB', 'AST']
    available_cols = [c for c in display_cols if c in nba_df.columns]
    print(nba_df[available_cols].head(10).to_string(index=False))
    
    # 7. 显示未匹配的球员
    unmatched = nba_df[nba_df['球员中文名'] == '']
    if len(unmatched) > 0:
        print(f"\n⚠️  未匹配到中文名的球员 ({len(unmatched)}名):")
        print(unmatched[['PLAYER_NAME', 'TEAM_ABBREVIATION']].head(20).to_string(index=False))
    
    return nba_df


def main():
    """主函数"""
    # 获取脚本所在目录的绝对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    nba_dir = os.path.join(base_dir, "output", "NBA官方统计")
    
    if not os.path.exists(nba_dir):
        print(f"[错误] 未找到目录: {nba_dir}")
        return
        
    # 扫描所有 NBA 统计文件
    files = [f for f in os.listdir(nba_dir) if f.startswith("NBA_完整统计_") and f.endswith(".csv") and "_含中文名" not in f]
    
    if not files:
        print(f"[提示] 未找到需要处理的文件 (在 {nba_dir})")
        return
        
    print(f"找到 {len(files)} 个文件需要处理: {files}")
    
    for filename in files:
        filepath = os.path.join(nba_dir, filename)
        add_chinese_names_to_nba_stats(filepath)


if __name__ == "__main__":
    main()
