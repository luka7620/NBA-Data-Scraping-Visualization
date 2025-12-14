# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 设置页面配置
st.set_page_config(
    page_title="NBA 数据分析仪表板",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据文件路径
DATA_FILE = "output/NBA官方统计/NBA_完整统计_2024-25_含中文名.csv"

# 术语映射字典
TERM_MAPPING = {
    'PTS': '得分', 'REB': '篮板', 'AST': '助攻', 'STL': '抢断', 'BLK': '盖帽',
    'TOV': '失误', 'GP': '出场', 'MIN': '分钟', 'FGM': '命中', 'FGA': '出手',
    'FG_PCT': '投篮%', 'FG3M': '三分命中', 'FG3A': '三分出手', 'FG3_PCT': '三分%',
    'FTM': '罚球命中', 'FTA': '罚球出手', 'FT_PCT': '罚球%', 'OREB': '前板',
    'DREB': '后板', 'PF': '犯规', 'TEAM_ABBREVIATION': '球队',
    'PLAYER_NAME': '球员(英)', '球员中文名': '球员'
}

# 术语解释
TERM_EXPLANATIONS = {
    '真实命中率 (TS%)': '衡量球员在两分球、三分球和罚球上的综合得分效率。计算公式考虑了三分球和罚球的价值。',
    '投篮命中率 (FG%)': '衡量球员整体投篮准度 (命中数/出手数)。',
    '三分命中率 (3P%)': '衡量球员三分球投射准度。',
    '罚球命中率 (FT%)': '衡量球员罚球准度。',
    '180俱乐部': '指投篮命中率≥50%，三分命中率≥40%，罚球命中率≥90%的精英射手群体。',
    '正负值 (+/-)': '球员在场期间球队净胜分（本数据集中可能未包含）。',
    '效率值': '综合得分、篮板、助攻等数据的综合评价指标。'
}

@st.cache_data
def load_data():
    """加载并预处理数据 (支持多赛季)"""
    data_dir = "output/NBA官方统计"
    if not os.path.exists(data_dir):
        return None
    
    all_files = [f for f in os.listdir(data_dir) if f.endswith("_含中文名.csv")]
    if not all_files:
        return None
        
    df_list = []
    for f in all_files:
        try:
            path = os.path.join(data_dir, f)
            temp_df = pd.read_csv(path)
            # 确保有赛季列
            if '赛季' not in temp_df.columns:
                # 尝试从文件名提取: NBA_完整统计_2024-25_含中文名.csv
                parts = f.split('_')
                if len(parts) >= 4:
                    temp_df['赛季'] = parts[2]
                else:
                    temp_df['赛季'] = 'Unknown'
            df_list.append(temp_df)
        except Exception as e:
            st.error(f"加载文件 {f} 失败: {e}")
            
    if not df_list:
        return None
        
    df = pd.concat(df_list, ignore_index=True)
    
    # 数据清洗与类型转换
    # 处理百分比列 (例如 "45.2%" -> 0.452)
    pct_cols = ['FG_PCT', 'FG3_PCT', 'FT_PCT']
    for col in pct_cols:
        if col in df.columns:
            # 如果已经是浮点数则跳过，如果是字符串则处理
            if df[col].dtype == 'object':
                df[col] = df[col].str.rstrip('%').astype('float')
            
            # 如果数值范围是 0-1，则转换为 0-100
            # 假设最大值不超过 1.5 (考虑到可能的异常值，但通常是 1.0) 且不全为 0
            if pd.api.types.is_numeric_dtype(df[col]):
                if df[col].max() <= 1.0 and df[col].max() > 0:
                    df[col] = df[col] * 100.0
    
    # 确保数值列是数值类型
    numeric_cols = ['GP', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # 加载并合并位置数据 (只用最新的位置信息)
    pos_map = load_position_data()
    df['位置'] = df['球员中文名'].map(pos_map).fillna('未知')
    
    return df

def load_position_data():
    """从球队名单加载位置信息"""
    position_map = {}
    roster_dir = "output/球队名单/整合数据"
    
    if not os.path.exists(roster_dir):
        return position_map
        
    for filename in os.listdir(roster_dir):
        if filename.endswith(".csv"):
            try:
                path = os.path.join(roster_dir, filename)
                # 只读取需要的列，避免错误
                df = pd.read_csv(path, usecols=['球员', '位置'])
                
                for _, row in df.iterrows():
                    name = row['球员']
                    pos = row['位置']
                    
                    if pd.notna(name) and pd.notna(pos):
                        # 简单映射: G->后卫, F->前锋, C->中锋
                        # 可能有 G-F, F-C 等组合
                        pos_cn = str(pos).replace('G', '后卫').replace('F', '前锋').replace('C', '中锋')
                        position_map[name] = pos_cn
            except Exception:
                continue
                
    return position_map

def normalize_data(df):
    """使用 Min-Max 归一化处理数据 (0-1范围)"""
    norm_df = df.copy()
    
    # 需要归一化的列
    metrics = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'OREB']
    
    for col in metrics:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            # 避免除以零
            if max_val > min_val:
                norm_df[f'{col}_NORM'] = (df[col] - min_val) / (max_val - min_val)
            else:
                norm_df[f'{col}_NORM'] = 0
            
    return norm_df

def calculate_advanced_scores(df):
    """
    计算高级雷达图评分 (0-100分制)
    基于 10 个维度的复合逻辑
    """
    score_df = df.copy()
    
    # 辅助排名函数 (0-1)
    def get_rank(col, ascending=True):
        if col not in score_df.columns:
            return 0
        if ascending:
            return score_df[col].rank(pct=True, method='min')
        else:
            return 1 - score_df[col].rank(pct=True, method='min')

    # 1. 突破 (Drive): 造犯规(PFD) + 罚球(FTA)
    score_df['突破_SCORE'] = (get_rank('PFD') + get_rank('FTA')) / 2 * 100
    
    # 2. 篮下 (Inside): 命中率(FG_PCT) + 前板(OREB)
    score_df['篮下_SCORE'] = (get_rank('FG_PCT') + get_rank('OREB')) / 2 * 100
    
    # 3. 背身 (Post): 2分命中(2PM) + 造犯规(PFD) + 前板(OREB)
    # 权重: 2PM(40%) + PFD(40%) + OREB(20%)
    score_df['背身_SCORE'] = (get_rank('2PM') * 0.4 + get_rank('PFD') * 0.4 + get_rank('OREB') * 0.2) * 100
    
    # 4. 中投 (Mid-Range): 2分命中数 (FGM - FG3M)
    # 确保先计算 2PM
    score_df['2PM'] = df['FGM'] - df['FG3M']
    score_df['中投_SCORE'] = get_rank('2PM') * 100
    
    # 5. 三分 (3PT): 命中率(FG3_PCT) + 命中数(FG3M)
    score_df['三分_SCORE'] = (get_rank('FG3_PCT') + get_rank('FG3M')) / 2 * 100
    
    # 6. 组织 (Playmaking): 助攻(AST) + 助攻率(AST_PCT) + 控制失误(TOV逆向)
    score_df['组织_SCORE'] = (get_rank('AST') + get_rank('AST_PCT') + get_rank('TOV', ascending=False)) / 3 * 100
    
    # 7. 内防 (Interior): 盖帽(BLK) + 后板(DREB)
    score_df['内防_SCORE'] = (get_rank('BLK') + get_rank('DREB')) / 2 * 100
    
    # 8. 外防 (Perimeter): 抢断(STL) + 防守效率(DEF_RATING逆向)
    score_df['外防_SCORE'] = (get_rank('STL') + get_rank('DEF_RATING', ascending=False)) / 2 * 100
    
    # 9. 抢断 (Steal): 抢断(STL)
    score_df['抢断_SCORE'] = get_rank('STL') * 100
    
    # 10. 篮板 (Rebound): 总板(REB) + 篮板率(REB_PCT)
    score_df['篮板_SCORE'] = (get_rank('REB') + get_rank('REB_PCT')) / 2 * 100
    
    return score_df

def show_overview(df):
    """显示数据概览"""
    st.header("🏀 联盟数据概览")
    
    # 关键指标
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("平均得分", f"{df['PTS'].mean():.1f}", help="联盟所有球员的场均得分")
    with col2:
        st.metric("平均篮板", f"{df['REB'].mean():.1f}", help="联盟所有球员的场均篮板")
    with col3:
        st.metric("平均助攻", f"{df['AST'].mean():.1f}", help="联盟所有球员的场均助攻")
    with col4:
        st.metric("平均抢断", f"{df['STL'].mean():.1f}", help="联盟所有球员的场均抢断")
    with col5:
        st.metric("平均盖帽", f"{df['BLK'].mean():.1f}", help="联盟所有球员的场均盖帽")
    
    st.divider()
    
    # 数据表
    st.subheader("📋 详细数据表")
    
    # 筛选区域
    col_filter_1, col_filter_2 = st.columns([1, 2])
    
    with col_filter_1:
        # 球队筛选
        all_teams = ['全部'] + sorted(df['TEAM_ABBREVIATION'].unique().tolist())
        selected_team = st.selectbox("筛选球队", all_teams, key="overview_team_filter")
        
    with col_filter_2:
        # 搜索框
        search_term = st.text_input("🔍 搜索球员", "")
    
    display_df = df.copy()
    
    # 应用球队筛选
    if selected_team != '全部':
        display_df = display_df[display_df['TEAM_ABBREVIATION'] == selected_team]
        
    # 应用搜索筛选
    if search_term:
        display_df = display_df[
            display_df['PLAYER_NAME'].str.contains(search_term, case=False, na=False) | 
            display_df['球员中文名'].str.contains(search_term, case=False, na=False) |
            display_df['TEAM_ABBREVIATION'].str.contains(search_term, case=False, na=False)
        ]
    
    # 格式化显示
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "球员中文名": "球员 (中文)",
            "PLAYER_NAME": "球员 (英文)",
            "TEAM_ABBREVIATION": "球队",
            "PTS": st.column_config.NumberColumn("得分", format="%.1f"),
            "REB": st.column_config.NumberColumn("篮板", format="%.1f"),
            "AST": st.column_config.NumberColumn("助攻", format="%.1f"),
            "STL": st.column_config.NumberColumn("抢断", format="%.1f"),
            "BLK": st.column_config.NumberColumn("盖帽", format="%.1f"),
            "FG_PCT": st.column_config.NumberColumn("投篮%", format="%.1f%%"),
            "FG3_PCT": st.column_config.NumberColumn("三分%", format="%.1f%%"),
            "FT_PCT": st.column_config.NumberColumn("罚球%", format="%.1f%%"),
        }
    )

def show_charts(df, full_df=None):
    """显示进阶图表"""
    if full_df is None:
        full_df = df
    st.header("📊 进阶图表分析")
    
    # 术语解释折叠栏
    with st.expander("💡 查看数据术语解释"):
        for term, desc in TERM_EXPLANATIONS.items():
            st.markdown(f"**{term}**: {desc}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["球队得分分布 (饼图)", "球员效率分析 (散点图)", "投篮分布 (180俱乐部)", "📈 生涯轨迹 (趋势图)"])
    
    with tab1:
        st.subheader("球队得分分布")
        team_list = sorted(df['TEAM_ABBREVIATION'].unique())
        selected_team = st.selectbox("选择球队", team_list)
        
        team_data = df[df['TEAM_ABBREVIATION'] == selected_team]
        
        # 饼图
        fig = px.pie(
            team_data, 
            values='PTS', 
            names='球员中文名', 
            title=f'{selected_team} 球员得分占比',
            hover_data=['PTS', 'GP', 'MIN'],
            labels={'球员中文名': '球员', 'PTS': '得分'}
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.subheader("球员效率分析")
        col1, col2, col3 = st.columns(3)
        
        # 选项映射
        axis_options = {
            'MIN': '出场时间', 'FGA': '出手数', 'FG3A': '三分出手', 'FTA': '罚球出手', 'TOV': '失误',
            'PTS': '得分', 'REB': '篮板', 'AST': '助攻', 'STL': '抢断', 'BLK': '盖帽'
        }
        
        with col1:
            x_sel = st.selectbox("X轴数据", list(axis_options.keys()), index=0, format_func=lambda x: f"{x} ({axis_options[x]})")
        with col2:
            y_sel = st.selectbox("Y轴数据", list(axis_options.keys()), index=5, format_func=lambda x: f"{x} ({axis_options[x]})")
        with col3:
            size_metric = st.selectbox("气泡大小", ['GP', 'PTS', 'None'], index=1, format_func=lambda x: '无' if x == 'None' else TERM_MAPPING.get(x, x))
            
        size_arg = size_metric if size_metric != 'None' else None
            
        # 交互选项
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            # 球队筛选
            teams = ['全部'] + sorted(df['TEAM_ABBREVIATION'].unique().tolist())
            sel_team = st.selectbox("筛选球队", teams)
            
        with c2:
            # 位置筛选
            positions = ['全部'] + sorted(df['位置'].unique().tolist())
            sel_pos = st.selectbox("筛选位置", positions)
            
        with c3:
            show_labels = st.checkbox("显示球员名字", value=False)
            
        with c4:
            # 搜索高亮 (基于筛选后的数据)
            # 先过滤数据用于搜索框
            temp_df = df.copy()
            if sel_team != '全部':
                temp_df = temp_df[temp_df['TEAM_ABBREVIATION'] == sel_team]
            if sel_pos != '全部':
                temp_df = temp_df[temp_df['位置'] == sel_pos]
                
            all_players = ['无'] + list(temp_df['球员中文名'].unique())
            highlight_player = st.selectbox("🔍 高亮搜索", all_players, index=0)

        # 数据准备 (应用筛选)
        plot_df = df.copy()
        if sel_team != '全部':
            plot_df = plot_df[plot_df['TEAM_ABBREVIATION'] == sel_team]
        if sel_pos != '全部':
            plot_df = plot_df[plot_df['位置'] == sel_pos]
        
        # 处理颜色和大小逻辑
        if highlight_player != '无':
            # 高亮模式
            plot_df['ColorGroup'] = plot_df['球员中文名'].apply(lambda x: x if x == highlight_player else '其他')
            plot_df['Size'] = plot_df['球员中文名'].apply(lambda x: 15 if x == highlight_player else 5)
            # 排序让高亮的点在最上层
            plot_df = plot_df.sort_values('ColorGroup', ascending=False)
            
            color_col = 'ColorGroup'
            color_map = {highlight_player: '#FF4B4B', '其他': '#E0E0E0'} # 红 vs 灰
            size_col = 'Size'
            size_max = 15
        else:
            # 普通模式
            color_col = 'TEAM_ABBREVIATION'
            color_map = None
            size_col = size_arg
            size_max = None # 默认

        # 绘图
        fig = px.scatter(
            plot_df, 
            x=x_sel, 
            y=y_sel, 
            size=size_col,
            color=color_col,
            color_discrete_map=color_map,
            hover_name='球员中文名',
            hover_data=['PLAYER_NAME', 'GP', 'PTS', 'REB', 'AST'],
            text='球员中文名' if show_labels else None,
            title=f'{TERM_MAPPING.get(y_sel, y_sel)} vs {TERM_MAPPING.get(x_sel, x_sel)}',
            labels={
                x_sel: TERM_MAPPING.get(x_sel, x_sel),
                y_sel: TERM_MAPPING.get(y_sel, y_sel),
                'TEAM_ABBREVIATION': '球队',
                'GP': '出场数',
                'ColorGroup': '球员'
            }
        )
        
        # 优化显示
        if show_labels:
            fig.update_traces(textposition='top center')
            
        if highlight_player != '无':
            fig.update_layout(showlegend=False)
            
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("180俱乐部追踪 (投篮≥50%, 三分≥40%, 罚球≥90%)")
        
        # 筛选出有一定出手数的球员 (避免数据样本太小)
        shooters = df[(df['FGA'] > 5) & (df['FG3A'] > 1) & (df['FTA'] > 1)].copy()
        
        # 创建子标签页
        subtab_2d, subtab_3d = st.tabs(["2D 平面分析", "3D 空间视图"])
        
        with subtab_2d:
            # 2D 散点图
            fig = px.scatter(
                shooters,
                x='FG3_PCT',
                y='FG_PCT',
                color='FT_PCT',
                size='PTS',
                hover_name='球员中文名',
                hover_data=['PLAYER_NAME', 'PTS', 'FG_PCT', 'FG3_PCT', 'FT_PCT'],
                title='投篮分布图 (颜色深=罚球准, 大小=得分高)',
                labels={
                    'FG_PCT': '投篮命中率 (FG%)',
                    'FG3_PCT': '三分命中率 (3P%)',
                    'FT_PCT': '罚球命中率 (FT%)',
                    'PTS': '场均得分'
                },
                color_continuous_scale='Blues', # 使用蓝色渐变
                range_x=[20, 60], # 设定合理的范围 (20%-60%)
                range_y=[30, 70], # (30%-70%)
                height=600
            )
            
            # 添加参考线
            fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50% FG", annotation_position="bottom right")
            fig.add_vline(x=40, line_dash="dash", line_color="red", annotation_text="40% 3P", annotation_position="top left")
            
            # 标记 180 区域 (右上角)
            fig.add_shape(
                type="rect",
                x0=40, y0=50, x1=60, y1=70,
                line=dict(color="green", width=0),
                fillcolor="green",
                opacity=0.1,
                layer="below"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        with subtab_3d:
            # 3D 散点图 (优化版)
            fig_3d = px.scatter_3d(
                shooters,
                x='FG_PCT',
                y='FG3_PCT',
                z='FT_PCT',
                color='PTS',
                size='PTS',
                hover_name='球员中文名',
                range_x=[30, 70],
                range_y=[20, 60],
                range_z=[50, 100],
                opacity=0.7, # 增加透明度
                title='投篮三项命中率空间分布',
                labels={
                    'FG_PCT': '投篮命中率',
                    'FG3_PCT': '三分命中率',
                    'FT_PCT': '罚球命中率',
                    'PTS': '得分'
                },
                height=700
            )
            st.plotly_chart(fig_3d, use_container_width=True)
        
        # 候选人表格 (共用)
        st.subheader("🎯 180俱乐部候选人 (接近或达标)")
        # 筛选逻辑: 接近 50-40-90 的球员
        candidates = shooters[
            (shooters['FG_PCT'] >= 48) & 
            (shooters['FG3_PCT'] >= 38) & 
            (shooters['FT_PCT'] >= 88)
        ].sort_values(['PTS'], ascending=False)
        
        st.dataframe(
            candidates[['球员中文名', 'TEAM_ABBREVIATION', 'PTS', 'FG_PCT', 'FG3_PCT', 'FT_PCT']],
            use_container_width=True,
            column_config={
                "FG_PCT": st.column_config.NumberColumn("投篮%", format="%.1f%%"),
                "FG3_PCT": st.column_config.NumberColumn("三分%", format="%.1f%%"),
                "FT_PCT": st.column_config.NumberColumn("罚球%", format="%.1f%%"),
            }
        )

    with tab4:
        st.subheader("📈 球员生涯数据追踪")
        
        # 搜索球员 (使用完整数据)
        # 过滤掉非字符串类型 (如 NaN)
        unique_names = full_df['球员中文名'].unique().tolist()
        all_players = sorted([x for x in unique_names if isinstance(x, str) and x.strip()])
        if not all_players:
            st.warning("无数据")
        else:
            # 简化selectbox，移除可能导致状态冲突的default_idx和key
            selected_player = st.selectbox("选择球员查看趋势", all_players)
            
            # 过滤该球员数据 (使用完整数据)
            player_history = full_df[full_df['球员中文名'] == selected_player].sort_values('赛季')
            
            if len(player_history) < 2:
                st.info(f"该球员仅有 {len(player_history)} 个赛季的数据，无法展示趋势。请爬取更多赛季数据。")
                st.dataframe(player_history)
            else:
                # 展示趋势图
                st.caption(f"当前展示: {selected_player} ({len(player_history)} 个赛季)")
                
                # 多维度折线图
                metrics_to_plot = ['PTS', 'REB', 'AST', 'FG_PCT', 'FG3_PCT']
                
                # 归一化以便在同一图表展示趋势 (可选，或者分面展示)
                # 这里选择分面展示或者多图
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 基础数据趋势
                    fig_base = px.line(
                        player_history, 
                        x='赛季', 
                        y=['PTS', 'REB', 'AST'],
                        markers=True,
                        title=f"{selected_player} - 基础数据趋势",
                        labels={'value': '数据', 'variable': '指标'}
                    )
                    st.plotly_chart(fig_base, use_container_width=True)
                    
                with col2:
                    # 命中率趋势
                    fig_pct = px.line(
                        player_history, 
                        x='赛季', 
                        y=['FG_PCT', 'FG3_PCT', 'FT_PCT'],
                        markers=True,
                        title=f"{selected_player} - 命中率趋势",
                        labels={'value': '命中率', 'variable': '指标'},
                        range_y=[0, 100] # 固定 0-100%
                    )
                    st.plotly_chart(fig_pct, use_container_width=True)
                
                # 详细数据表
                st.dataframe(
                    player_history[['赛季', 'TEAM_ABBREVIATION', 'GP', 'PTS', 'REB', 'AST', 'FG_PCT', 'FG3_PCT', 'FT_PCT']],
                    use_container_width=True,
                    hide_index=True
                )

def show_player_comparison(df, full_df=None):
    """球员对比功能"""
    if full_df is None:
        full_df = df
        
    st.header("🆚 球员对比")
    st.caption("💡 支持跨赛季对比：可以对比同一球员在不同赛季的表现")
    
    # 获取可用赛季列表
    if '赛季' in full_df.columns:
        all_seasons = sorted(full_df['赛季'].unique().tolist(), reverse=True)
    else:
        all_seasons = []
    
    col1, col2 = st.columns(2)
    
    # ---------- 球员 1 ----------
    with col1:
        st.subheader("🔵 球员 1")
        
        # 赛季选择
        if all_seasons:
            p1_season = st.selectbox("选择赛季 (1)", all_seasons, key="p1_season")
            p1_df = full_df[full_df['赛季'] == p1_season].copy()
        else:
            p1_df = df.copy()
            
        # 球队和位置筛选
        p1_all_teams = ['全部'] + sorted(p1_df['TEAM_ABBREVIATION'].unique().tolist())
        p1_all_positions = ['全部'] + sorted(p1_df['位置'].unique().tolist())
        
        p1_team = st.selectbox("筛选球队 (1)", p1_all_teams, key="p1_team")
        p1_pos = st.selectbox("筛选位置 (1)", p1_all_positions, key="p1_pos")
        
        # 应用筛选
        if p1_team != '全部':
            p1_df = p1_df[p1_df['TEAM_ABBREVIATION'] == p1_team]
        if p1_pos != '全部':
            p1_df = p1_df[p1_df['位置'] == p1_pos]
            
        p1_options = p1_df['球员中文名'].unique()
        if len(p1_options) == 0:
            st.warning("无匹配球员")
            player1_name = None
            p1_season_display = None
        else:
            player1_name = st.selectbox("选择球员 1", p1_options, index=0, key="p1_name")
            p1_season_display = p1_season if all_seasons else "当前赛季"
            
    # ---------- 球员 2 ----------
    with col2:
        st.subheader("🔴 球员 2")
        
        # 赛季选择
        if all_seasons:
            # 默认选择不同的赛季（如果有多个赛季）
            default_p2_season_idx = 1 if len(all_seasons) > 1 else 0
            p2_season = st.selectbox("选择赛季 (2)", all_seasons, index=default_p2_season_idx, key="p2_season")
            p2_df = full_df[full_df['赛季'] == p2_season].copy()
        else:
            p2_df = df.copy()
            
        # 球队和位置筛选
        p2_all_teams = ['全部'] + sorted(p2_df['TEAM_ABBREVIATION'].unique().tolist())
        p2_all_positions = ['全部'] + sorted(p2_df['位置'].unique().tolist())
        
        p2_team = st.selectbox("筛选球队 (2)", p2_all_teams, key="p2_team")
        p2_pos = st.selectbox("筛选位置 (2)", p2_all_positions, key="p2_pos")
        
        # 应用筛选
        if p2_team != '全部':
            p2_df = p2_df[p2_df['TEAM_ABBREVIATION'] == p2_team]
        if p2_pos != '全部':
            p2_df = p2_df[p2_df['位置'] == p2_pos]
            
        p2_options = p2_df['球员中文名'].unique()
        if len(p2_options) == 0:
            st.warning("无匹配球员")
            player2_name = None
            p2_season_display = None
        else:
            # 尝试默认选第二个不同的人（但同赛季可以选相同球员）
            default_idx = 0
            if len(p2_options) > 1 and player1_name in p2_options and p1_season == p2_season:
                if p2_options[0] == player1_name:
                    default_idx = 1
            
            player2_name = st.selectbox("选择球员 2", p2_options, index=default_idx, key="p2_name")
            p2_season_display = p2_season if all_seasons else "当前赛季"
        
    if player1_name and player2_name:
        # 从各自的赛季数据中提取球员数据
        # 合并两个赛季的数据以便统一计算排名
        combined_df = pd.concat([p1_df, p2_df], ignore_index=True)
        
        # 预先计算 2PM
        combined_df['2PM'] = combined_df['FGM'] - combined_df['FG3M']
        
        # 计算高级评分
        score_df = calculate_advanced_scores(combined_df)
        
        # 提取球员数据（需要考虑同名不同赛季的情况）
        p1_score = score_df[(score_df['球员中文名'] == player1_name) & (score_df['赛季'] == p1_season)].iloc[0]
        p2_score = score_df[(score_df['球员中文名'] == player2_name) & (score_df['赛季'] == p2_season)].iloc[0]
        
        p1_real = combined_df[(combined_df['球员中文名'] == player1_name) & (combined_df['赛季'] == p1_season)].iloc[0]
        p2_real = combined_df[(combined_df['球员中文名'] == player2_name) & (combined_df['赛季'] == p2_season)].iloc[0]
        
        # 1. 高级雷达图
        st.subheader("全能属性对比 (2K风格 - 10维复合评分)")
        
        # 定义维度映射配置
        # (显示名称, 评分列名, 核心展示数据列名)
        radar_config = [
            ("突破", "突破_SCORE", "PFD"),
            ("篮下", "篮下_SCORE", "FG_PCT"),
            ("背身", "背身_SCORE", "PTS"),
            ("中投", "中投_SCORE", "2PM"), # 使用 2PM
            ("三分", "三分_SCORE", "FG3_PCT"),
            ("组织", "组织_SCORE", "AST"),
            ("内防", "内防_SCORE", "BLK"),
            ("外防", "外防_SCORE", "DEF_RATING"),
            ("抢断", "抢断_SCORE", "STL"),
            ("篮板", "篮板_SCORE", "REB"),
        ]
        
        categories = [item[0] for item in radar_config]
        score_cols = [item[1] for item in radar_config]
        data_cols = [item[2] for item in radar_config]
        
        fig = go.Figure()
        
        # 构建带赛季的球员名
        p1_display = f"{player1_name} ({p1_season_display})"
        p2_display = f"{player2_name} ({p2_season_display})"
        
        # 球员 1 (红色)
        fig.add_trace(go.Scatterpolar(
            r=[p1_score[c] for c in score_cols],
            theta=categories,
            fill='toself',
            name=p1_display,
            line_color='#FF4B4B',
            opacity=0.6, # 半透明
            hoveron='points', # 仅点触发悬停，防止填充遮挡
            mode='lines+markers',
            # 自定义数据: 原始值
            customdata=[p1_real[c] for c in data_cols],
            hovertemplate="<b>%{theta}</b><br>核心数据: %{customdata:.1f}<br>联盟评分: %{r:.0f}<extra></extra>"
        ))
        
        # 球员 2 (蓝色)
        fig.add_trace(go.Scatterpolar(
            r=[p2_score[c] for c in score_cols],
            theta=categories,
            fill='toself',
            name=p2_display,
            line_color='#1E88E5',
            opacity=0.6, # 半透明
            hoveron='points', # 仅点触发悬停
            mode='lines+markers',
            # 自定义数据: 原始值
            customdata=[p2_real[c] for c in data_cols],
            hovertemplate="<b>%{theta}</b><br>核心数据: %{customdata:.1f}<br>联盟评分: %{r:.0f}<extra></extra>"
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[0, 100], # 固定 0-100
                    tickfont=dict(size=10, color="gray"),
                ),
                angularaxis=dict(
                    tickfont=dict(size=14, color="black"), # 加大字体
                    rotation=90, # 旋转起始角度
                    direction="clockwise"
                )
            ),
            showlegend=True,
            height=600 # 增加高度
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. 详细数据对比表
        st.subheader("详细数据对比")
        
        # 定义要对比的列
        comp_cols = [
            'GP', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 
            'FG_PCT', 'FG3_PCT', 'FT_PCT',
            'OREB', 'DREB'
        ]
        
        # 构建对比数据
        comp_data = []
        for col in comp_cols:
            val1 = p1_real.get(col, 0)
            val2 = p2_real.get(col, 0)
            
            # 格式化
            if 'PCT' in col:
                v1_str = f"{val1:.1%}"
                v2_str = f"{val2:.1%}"
            else:
                v1_str = f"{val1:.1f}"
                v2_str = f"{val2:.1f}"
                
            # 计算差异
            diff = val1 - val2
            if 'PCT' in col:
                diff_str = f"{diff:+.1%}"
            else:
                diff_str = f"{diff:+.1f}"
                
            comp_data.append({
                "数据项": TERM_MAPPING.get(col, col),
                player1_name: v1_str,
                player2_name: v2_str,
                "差异": diff_str
            })
            
        st.table(pd.DataFrame(comp_data).set_index("数据项"))

def show_team_analysis(df, full_df=None):
    """球队分析"""
    if full_df is None:
        full_df = df
        
    st.header("🏢 球队分析")
    
    # 赛季选择器
    if '赛季' in full_df.columns:
        all_seasons = sorted(full_df['赛季'].unique().tolist(), reverse=True)
        selected_season = st.selectbox("选择赛季", all_seasons, key="team_analysis_season")
        df = full_df[full_df['赛季'] == selected_season].copy()
        st.caption(f"当前分析赛季: {selected_season}")
    
    # 计算球队平均数据
    team_stats = df.groupby('TEAM_ABBREVIATION')[['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']].mean().reset_index()
    
    st.subheader("各队场均数据对比")
    
    metric_options = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    metric = st.selectbox("选择对比指标", metric_options, format_func=lambda x: TERM_MAPPING.get(x, x))
    
    # 排序
    team_stats = team_stats.sort_values(metric, ascending=False)
    
    fig = px.bar(
        team_stats,
        x='TEAM_ABBREVIATION',
        y=metric,
        color=metric,
        title=f'各球队平均{TERM_MAPPING.get(metric, metric)}排行',
        text_auto='.1f',
        labels={
            'TEAM_ABBREVIATION': '球队',
            metric: TERM_MAPPING.get(metric, metric)
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 散点图
    st.subheader("球队风格分布 (得分 vs 篮板)")
    fig2 = px.scatter(
        team_stats,
        x='PTS',
        y='REB',
        color='TEAM_ABBREVIATION',
        text='TEAM_ABBREVIATION',
        size='AST',
        title='球队场均得分 vs 篮板 (气泡大小=助攻)',
        labels={
            'PTS': '场均得分',
            'REB': '场均篮板',
            'AST': '场均助攻',
            'TEAM_ABBREVIATION': '球队'
        }
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 3. 球队综合实力对比 (雷达图)
    st.divider()
    st.subheader("⚔️ 球队综合实力对比")
    
    # 计算球队维度的百分位排名
    # 使用之前计算好的 team_stats (包含均值)
    team_score_df = team_stats.copy()
    
    # 定义要对比的维度
    # 进攻(PTS), 篮板(REB), 助攻(AST), 抢断(STL), 盖帽(BLK), 控制(TOV-逆向)
    radar_metrics = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    
    for col in radar_metrics:
        if col == 'TOV':
            # 失误越少越好，所以用 1 - rank
            team_score_df[f'{col}_SCORE'] = (1 - team_score_df[col].rank(pct=True)) * 100
        else:
            team_score_df[f'{col}_SCORE'] = team_score_df[col].rank(pct=True) * 100
            
    # 选择球队
    c1, c2 = st.columns(2)
    all_teams = sorted(team_stats['TEAM_ABBREVIATION'].unique())
    
    with c1:
        t1_name = st.selectbox("选择球队 1", all_teams, index=0, key="t1_radar")
    with c2:
        default_idx = 1 if len(all_teams) > 1 else 0
        t2_name = st.selectbox("选择球队 2", all_teams, index=default_idx, key="t2_radar")
        
    if t1_name and t2_name:
        t1_score = team_score_df[team_score_df['TEAM_ABBREVIATION'] == t1_name].iloc[0]
        t2_score = team_score_df[team_score_df['TEAM_ABBREVIATION'] == t2_name].iloc[0]
        
        t1_real = team_stats[team_stats['TEAM_ABBREVIATION'] == t1_name].iloc[0]
        t2_real = team_stats[team_stats['TEAM_ABBREVIATION'] == t2_name].iloc[0]
        
        # 绘图
        fig_radar = go.Figure()
        
        labels = [TERM_MAPPING.get(c, c) for c in radar_metrics]
        
        # 球队 1
        fig_radar.add_trace(go.Scatterpolar(
            r=[t1_score[f'{c}_SCORE'] for c in radar_metrics],
            theta=labels,
            fill='toself',
            name=t1_name,
            line_color='#FF4B4B',
            opacity=0.6,
            hoveron='points',
            mode='lines+markers',
            customdata=[t1_real[c] for c in radar_metrics],
            hovertemplate="<b>%{theta}</b><br>场均数据: %{customdata:.1f}<br>联盟排名: 超过 %{r:.1f}% 的球队<extra></extra>"
        ))
        
        # 球队 2
        fig_radar.add_trace(go.Scatterpolar(
            r=[t2_score[f'{c}_SCORE'] for c in radar_metrics],
            theta=labels,
            fill='toself',
            name=t2_name,
            line_color='#1E88E5',
            opacity=0.6,
            hoveron='points',
            mode='lines+markers',
            customdata=[t2_real[c] for c in radar_metrics],
            hovertemplate="<b>%{theta}</b><br>场均数据: %{customdata:.1f}<br>联盟排名: 超过 %{r:.1f}% 的球队<extra></extra>"
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[0, 100],
                    tickfont=dict(size=10, color="gray"),
                ),
                angularaxis=dict(
                    tickfont=dict(size=14, color="black"),
                    rotation=90,
                    direction="clockwise"
                )
            ),
            showlegend=True,
            height=500,
            title="球队攻防能力对比 (基于场均数据排名)"
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)





import json

# ... (imports)

# 数据文件路径
DATA_FILE = "output/NBA官方统计/NBA_完整统计_2024-25_含中文名.csv"
CUSTOM_PLAYERS_FILE = "custom_players.json"

# ... (TERM_MAPPING, TERM_EXPLANATIONS)

def load_custom_players():
    """从 JSON 文件加载自建球员数据"""
    if os.path.exists(CUSTOM_PLAYERS_FILE):
        try:
            with open(CUSTOM_PLAYERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载自建球员数据失败: {e}")
            return {}
    return {}

def save_custom_players(players):
    """保存自建球员数据到 JSON 文件"""
    try:
        with open(CUSTOM_PLAYERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"保存自建球员数据失败: {e}")

# ... (load_data, load_position_data, normalize_data, calculate_advanced_scores, show_overview, show_charts, show_player_comparison, show_team_analysis)

def show_playground(df):
    """娱乐板块: 自建球员对比"""
    st.header("🎮 娱乐：自建球员实验室")
    st.caption("在这里，你可以创造属于你的超级球员，并将他与 NBA 现役球员一决高下！")
    
    # 初始化 session_state (优先从文件加载)
    if 'custom_players' not in st.session_state or not st.session_state['custom_players']:
        st.session_state['custom_players'] = load_custom_players()
        
    # --- 侧边栏：创建球员 ---
    with st.sidebar:
        st.header("🛠️ 捏人系统")
        
        # 模式选择: 创建 vs 编辑
        mode = st.radio("模式", ["创建新球员", "编辑现有球员"], horizontal=True)
        
        # 默认值初始化
        default_values = {
            'name': "My Player", 'pos': "后卫", 'team': "CUSTOM", 'team_mode': "创建新球队",
            'pts': 20.0, 'ast': 5.0, 'oreb': 1.0, 'tov': 2.0,
            'fgm': 8.0, 'fg3m': 2.0, 'ftm': 4.0,
            'fga': 16.0, 'fg3a': 6.0, 'fta': 5.0,
            'dreb': 4.0, 'stl': 1.0, 'blk': 0.5,
            'pfd': 4.0, 'def_rtg': 110.0, 'ast_pct': 0.2, 'reb_pct': 0.1
        }
        
        selected_player_key = None
        if mode == "编辑现有球员":
            # 获取现有自建球员列表
            custom_player_names = list(st.session_state['custom_players'].keys())
            if custom_player_names:
                selected_player_key = st.selectbox("选择要编辑的球员", custom_player_names)
                # 加载数据
                p_data = st.session_state['custom_players'][selected_player_key]
                
                default_values['name'] = p_data['PLAYER_NAME']
                default_values['pos'] = p_data['位置']
                default_values['team'] = p_data['TEAM_ABBREVIATION']
                # 判断球队模式
                all_teams_list = sorted(df['TEAM_ABBREVIATION'].unique().tolist())
                if p_data['TEAM_ABBREVIATION'] in all_teams_list:
                    default_values['team_mode'] = "加入现役球队"
                else:
                    default_values['team_mode'] = "创建新球队"
                    
                default_values['pts'] = float(p_data.get('PTS', 0))
                default_values['ast'] = float(p_data.get('AST', 0))
                default_values['oreb'] = float(p_data.get('OREB', 0))
                default_values['tov'] = float(p_data.get('TOV', 0))
                
                default_values['fgm'] = float(p_data.get('FGM', 0))
                default_values['fg3m'] = float(p_data.get('FG3M', 0))
                default_values['ftm'] = float(p_data.get('FTM', 0))
                
                default_values['fga'] = float(p_data.get('FGA', 0))
                default_values['fg3a'] = float(p_data.get('FG3A', 0))
                default_values['fta'] = float(p_data.get('FTA', 0))
                
                default_values['dreb'] = float(p_data.get('DREB', 0))
                default_values['stl'] = float(p_data.get('STL', 0))
                default_values['blk'] = float(p_data.get('BLK', 0))
                
                default_values['pfd'] = float(p_data.get('PFD', 0))
                default_values['def_rtg'] = float(p_data.get('DEF_RATING', 110))
                default_values['ast_pct'] = float(p_data.get('AST_PCT', 0.2))
                default_values['reb_pct'] = float(p_data.get('REB_PCT', 0.1))
            else:
                st.warning("暂无自建球员可编辑")

        # 球队选择模式 (放在表单外以支持实时刷新)
        st.subheader("球队归属")
        team_choice_mode = st.radio("选择模式", ["加入现役球队", "创建新球队"], horizontal=True, index=0 if default_values['team_mode'] == "加入现役球队" else 1)
        
        with st.form("create_player_form"):
            st.subheader("基础信息")
            c_name = st.text_input("球员名字", default_values['name'])
            # 锁定名字编辑如果是在编辑模式 (可选，为了简单起见允许修改，修改即创建新/覆盖)
            
            pos_index = ["后卫", "前锋", "中锋"].index(default_values['pos']) if default_values['pos'] in ["后卫", "前锋", "中锋"] else 0
            c_pos = st.selectbox("位置", ["后卫", "前锋", "中锋"], index=pos_index)
            
            # 根据外部选择显示不同的输入控件
            # 获取所有现役球队
            real_teams = sorted(df['TEAM_ABBREVIATION'].unique().tolist())
            # 获取所有自建球队 (去重)
            custom_teams = sorted(list(set([p['TEAM_ABBREVIATION'] for p in st.session_state['custom_players'].values()])))
            # 合并列表 (现役在前，自建在后，去重)
            all_teams = sorted(list(set(real_teams + custom_teams)))
            
            if team_choice_mode == "加入现役球队":
                try:
                    team_index = all_teams.index(default_values['team'])
                except:
                    team_index = 0
                c_team = st.selectbox("选择球队", all_teams, index=team_index)
            else:
                c_team = st.text_input("输入球队代码 (如 MYTEAM)", default_values['team']).upper()
            
            st.subheader("进攻数据 (场均)")
            c_pts = st.number_input("得分 (PTS)", 0.0, 100.0, default_values['pts'], step=0.1)
            c_ast = st.number_input("助攻 (AST)", 0.0, 50.0, default_values['ast'], step=0.1)
            c_oreb = st.number_input("前场篮板 (OREB)", 0.0, 20.0, default_values['oreb'], step=0.1)
            c_tov = st.number_input("失误 (TOV)", 0.0, 20.0, default_values['tov'], step=0.1)
            
            st.subheader("投射数据 (场均)")
            c1, c2 = st.columns(2)
            with c1:
                c_fgm = st.number_input("命中 (FGM)", 0.0, 50.0, default_values['fgm'], step=0.1)
                c_fg3m = st.number_input("三分命中", 0.0, 30.0, default_values['fg3m'], step=0.1)
                c_ftm = st.number_input("罚球命中", 0.0, 30.0, default_values['ftm'], step=0.1)
            with c2:
                c_fga = st.number_input("出手 (FGA)", 0.0, 100.0, default_values['fga'], step=0.1)
                c_fg3a = st.number_input("三分出手", 0.0, 50.0, default_values['fg3a'], step=0.1)
                c_fta = st.number_input("罚球出手", 0.0, 50.0, default_values['fta'], step=0.1)
                
            st.subheader("防守数据 (场均)")
            c_dreb = st.number_input("后场篮板 (DREB)", 0.0, 30.0, default_values['dreb'], step=0.1)
            c_stl = st.number_input("抢断 (STL)", 0.0, 10.0, default_values['stl'], step=0.1)
            c_blk = st.number_input("盖帽 (BLK)", 0.0, 10.0, default_values['blk'], step=0.1)
            
            st.subheader("高阶/隐藏属性 (模拟)")
            c_pfd = st.number_input("造犯规 (PFD)", 0.0, 20.0, default_values['pfd'], step=0.1)
            c_def_rtg = st.slider("防守效率 (越低越好)", 80.0, 120.0, default_values['def_rtg'], step=0.1, help="联盟平均约 115，DPOY 级别约 100")
            c_ast_pct = st.slider("助攻率 (AST%)", 0.0, 1.0, default_values['ast_pct'], step=0.01)
            c_reb_pct = st.slider("篮板率 (REB%)", 0.0, 1.0, default_values['reb_pct'], step=0.01)
            
            submitted = st.form_submit_button("保存/更新球员")
            
            if submitted:
                # 自动计算衍生数据
                c_fg_pct = c_fgm / c_fga if c_fga > 0 else 0
                c_fg3_pct = c_fg3m / c_fg3a if c_fg3a > 0 else 0
                c_ft_pct = c_ftm / c_fta if c_fta > 0 else 0
                c_reb = c_oreb + c_dreb
                
                player_data = {
                    '球员中文名': c_name,
                    'PLAYER_NAME': c_name,
                    'TEAM_ABBREVIATION': c_team, # 使用选择的球队
                    '位置': c_pos,
                    'PTS': c_pts, 'AST': c_ast, 'OREB': c_oreb, 'DREB': c_dreb, 'REB': c_reb,
                    'TOV': c_tov, 'STL': c_stl, 'BLK': c_blk,
                    'FGM': c_fgm, 'FGA': c_fga, 'FG_PCT': c_fg_pct,
                    'FG3M': c_fg3m, 'FG3A': c_fg3a, 'FG3_PCT': c_fg3_pct,
                    'FTM': c_ftm, 'FTA': c_fta, 'FT_PCT': c_ft_pct,
                    'PFD': c_pfd, 'DEF_RATING': c_def_rtg,
                    'AST_PCT': c_ast_pct, 'REB_PCT': c_reb_pct,
                    '2PM': c_fgm - c_fg3m # 预计算
                }
                st.session_state['custom_players'][c_name] = player_data
                save_custom_players(st.session_state['custom_players']) # 保存到文件
                st.success(f"球员 {c_name} 已保存到 {c_team}！")
                

    # --- 主界面：对比 ---
    
    # 1. 准备数据 (合并 现役 + 自建)
    # 将自建球员转换为 DataFrame
    if st.session_state['custom_players']:
        custom_df = pd.DataFrame(st.session_state['custom_players'].values())
        # 确保列对齐，缺失的列补0或NaN (不影响计算排名的列即可)
        combined_df = pd.concat([df, custom_df], ignore_index=True)
    else:
        combined_df = df.copy()
        st.info("👈 请先在左侧侧边栏创建一个自建球员")
        
    # 2. 选择球员
    st.subheader("⚔️ 巅峰对决")
    
    # 获取所有可用球队 (包括自建球队)
    all_teams_available = ['全部'] + sorted(combined_df['TEAM_ABBREVIATION'].unique().tolist())
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔵 挑战者 (球员 1)")
        # 球队筛选 1
        filter_team_1 = st.selectbox("筛选球队", all_teams_available, key="pg_filter_team_1")
        
        # 根据球队筛选球员
        if filter_team_1 != '全部':
            p1_options = combined_df[combined_df['TEAM_ABBREVIATION'] == filter_team_1]['球员中文名'].unique().tolist()
        else:
            # 默认显示自建球员 + 现役
            custom_names = [p['球员中文名'] for p in st.session_state['custom_players'].values()]
            real_names = [x for x in df['球员中文名'].unique().tolist() if isinstance(x, str)]
            p1_options = custom_names + sorted(real_names)
            
        p1_name = st.selectbox("选择球员", p1_options, index=0, key="pg_p1")

    with col2:
        st.markdown("#### 🔴 守擂者 (球员 2)")
        # 球队筛选 2
        filter_team_2 = st.selectbox("筛选球队", all_teams_available, key="pg_filter_team_2")
        
        # 根据球队筛选球员
        if filter_team_2 != '全部':
            p2_options = combined_df[combined_df['TEAM_ABBREVIATION'] == filter_team_2]['球员中文名'].unique().tolist()
        else:
            custom_names = [p['球员中文名'] for p in st.session_state['custom_players'].values()]
            real_names = [x for x in df['球员中文名'].unique().tolist() if isinstance(x, str)]
            p2_options = custom_names + sorted(real_names)
            
        # 默认选个詹姆斯当靶子
        default_idx = 0
        if filter_team_2 == '全部':
            try:
                lbj_idx = p2_options.index("勒布朗-詹姆斯")
                default_idx = lbj_idx
            except:
                default_idx = 1 if len(p2_options) > 1 else 0
                
        p2_name = st.selectbox("选择球员", p2_options, index=default_idx, key="pg_p2")
        
    if p1_name and p2_name:
        # 3. 计算评分 (在合并后的数据上计算，这样自建球员的排名才是基于全联盟的)
        # 强制重新计算 2PM (因为合并后现役球员的 2PM 列可能是 NaN)
        combined_df['2PM'] = combined_df['FGM'] - combined_df['FG3M']
            
        score_df = calculate_advanced_scores(combined_df)
        
        # 提取数据
        p1_score = score_df[score_df['球员中文名'] == p1_name].iloc[0]
        p2_score = score_df[score_df['球员中文名'] == p2_name].iloc[0]
        
        p1_real = combined_df[combined_df['球员中文名'] == p1_name].iloc[0]
        p2_real = combined_df[combined_df['球员中文名'] == p2_name].iloc[0]
        
        # 4. 绘制雷达图 (复用逻辑)
        radar_config = [
            ("突破", "突破_SCORE", "PFD"),
            ("篮下", "篮下_SCORE", "FG_PCT"),
            ("背身", "背身_SCORE", "PTS"),
            ("中投", "中投_SCORE", "2PM"),
            ("三分", "三分_SCORE", "FG3_PCT"),
            ("组织", "组织_SCORE", "AST"),
            ("内防", "内防_SCORE", "BLK"),
            ("外防", "外防_SCORE", "DEF_RATING"),
            ("抢断", "抢断_SCORE", "STL"),
            ("篮板", "篮板_SCORE", "REB"),
        ]
        
        categories = [item[0] for item in radar_config]
        score_cols = [item[1] for item in radar_config]
        data_cols = [item[2] for item in radar_config]
        
        fig = go.Figure()
        
        # 球员 1
        fig.add_trace(go.Scatterpolar(
            r=[p1_score[c] for c in score_cols],
            theta=categories,
            fill='toself',
            name=p1_name,
            line_color='#FF4B4B',
            opacity=0.6,
            hoveron='points',
            mode='lines+markers',
            customdata=[p1_real[c] for c in data_cols],
            hovertemplate="<b>%{theta}</b><br>核心数据: %{customdata:.1f}<br>能力评分: %{r:.0f} (超过 %{r:.0f}% 球员)<extra></extra>"
        ))
        
        # 球员 2
        fig.add_trace(go.Scatterpolar(
            r=[p2_score[c] for c in score_cols],
            theta=categories,
            fill='toself',
            name=p2_name,
            line_color='#1E88E5',
            opacity=0.6,
            hoveron='points',
            mode='lines+markers',
            customdata=[p2_real[c] for c in data_cols],
            hovertemplate="<b>%{theta}</b><br>核心数据: %{customdata:.1f}<br>能力评分: %{r:.0f} (超过 %{r:.0f}% 球员)<extra></extra>"
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10, color="gray")),
                angularaxis=dict(tickfont=dict(size=14, color="black"), rotation=90, direction="clockwise")
            ),
            showlegend=True,
            height=600,
            title=f"{p1_name} vs {p2_name} 能力对比"
        )
        
        st.plotly_chart(fig, use_container_width=True)


def main():
    # 动态标题将在下方根据赛季显示
    
    df = load_data()
    original_df = df.copy() if df is not None else None
    
    if df is None:
        st.error(f"无法找到数据文件: {DATA_FILE}")
        st.info("请先运行爬虫获取数据。")
        return
    
    # 侧边栏导航
    st.sidebar.title("导航")
    page = st.sidebar.radio("选择页面", ["数据概览", "图表分析", "球员对比", "球队分析", "🎮 娱乐：自建球员"])
    
    st.sidebar.divider()
    
    # 赛季筛选 (新增)
    if '赛季' in df.columns:
        all_seasons = sorted(df['赛季'].unique().tolist(), reverse=True)
        selected_season = st.sidebar.selectbox("选择赛季", all_seasons, index=0)
        
        # 全局过滤
        df = df[df['赛季'] == selected_season].copy()
        st.sidebar.caption(f"当前展示: {selected_season} 赛季 ({len(df)} 名球员)")
        
        # 动态标题
        st.title("NBA 数据分析仪表板")
    else:
        st.sidebar.warning("数据中未找到赛季信息")
        st.title("NBA 数据分析仪表板")

    # 全局筛选 (Removed as per instruction, but keeping the original comment for context if it was meant to be kept)
    # st.sidebar.divider()
    # st.sidebar.subheader("数据筛选")
    # min_gp = st.sidebar.slider("最少出场场次", 0, int(df['GP'].max()), 5)
    
    # 过滤数据 (Removed as per instruction)
    # filtered_df = df[df['GP'] >= min_gp]
    # st.sidebar.text(f"当前展示: {len(filtered_df)} 名球员")
    
    if page == "数据概览":
        show_overview(df)
    elif page == "图表分析":
        show_charts(df, full_df=original_df)
    elif page == "球员对比":
        show_player_comparison(df, full_df=original_df)
    elif page == "球队分析":
        show_team_analysis(df, full_df=original_df)
    elif page == "🎮 娱乐：自建球员":
        show_playground(df)

if __name__ == "__main__":
    main()
