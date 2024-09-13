import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyecharts.charts import WordCloud,Bar,Line,Pie,PictorialBar
from pyecharts.globals import SymbolType,ThemeType
from streamlit_echarts import st_pyecharts
import streamlit.components.v1 as components
from pyecharts import options as opts
from datetime import datetime, timedelta, date
import json
from phone import Phone
from pyecharts.charts import Map
from pyecharts.charts import Bar3D

# 设置页面配置
st.set_page_config(page_title="QRV呼入分析222", layout="wide")

plt.rcParams['font.sans-serif'] = ['SimHei']

# 加载CSS文件
with open("styles.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 加载json文件
with open("symbol.json", "r", encoding="utf-8") as f2:
    symbols = json.load(f2)

# ======== 读取Excel文件 ========
file_path = './每天分析.xlsx'
df = pd.read_excel(file_path, sheet_name='总统计')
sheets2 = pd.ExcelFile(file_path).sheet_names
sheet1_name = sheets2[-2]
df_sheet2 = pd.read_excel(file_path, sheet_name=sheet1_name)

sheet2_name = sheets2[-1]
df_sheet3 = pd.read_excel(file_path, sheet_name=sheet2_name)
# ======== 读取Excel文件 ========

def render_header_and_date_selector(header_title, date_range_data, selectbox_key, date_input_key, show_selectbox=True,
                                    show_date_selector=True):
    col_header, col_date_selector = st.columns([2, 1])

    with col_header:
        st.markdown(f'''
            <div class="header data-title">{header_title}
                <span class="icon-container">
                    <span class="icon">!</span>
                </span>
            </div>
        ''', unsafe_allow_html=True)

    if show_date_selector:
        with col_date_selector:
            col_topic1, col_topic2 = st.columns([1, 2])
            if show_selectbox:
                with col_topic1:
                    st.selectbox('', ['每日', '每周', '每月'], key=selectbox_key)

            with col_topic2:
                st.date_input('', date_range_data, format="YYYY/MM/DD", key=date_input_key)


def render_header_and_date_selector_organization(header_title, date_range_data, selectbox_key, date_input_key):
    col_header, col_date_selector = st.columns([2, 1])

    with col_header:
        st.markdown(f'''
            <div class="header data-title">{header_title}
                <span class="icon-container">
                    <span class="icon">!</span>
                </span>
            </div>
        ''', unsafe_allow_html=True)

    with col_date_selector:
        col_topic1, col_topic2 = st.columns([1, 2])
        with col_topic1:
            st.selectbox('', ['明楼', '机构b', '机构c'], key=selectbox_key)

        with col_topic2:
            st.date_input('', date_range_data, format="YYYY/MM/DD", key=date_input_key)


def query_data(defile, date_range, selectbox_value='每日'):
    defile['时间'] = pd.to_datetime(defile['时间'], format='%Y-%m-%d')

    if date_range is None or len(date_range) != 2:
        return defile.copy()

    start_date, end_date = date_range
    if not start_date or not end_date:
        raise ValueError("Invalid date range")
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    mask = (defile['时间'] >= start_date) & (defile['时间'] <= end_date)
    filtered_df = defile.loc[mask]

    if filtered_df.empty:
        return pd.DataFrame()

    # Exclude the '时间' column before grouping and summing
    other_columns = [col for col in filtered_df.columns if col != '时间']
    grouped_df = None

    if selectbox_value == '每日':
        grouped_df = filtered_df.groupby(filtered_df['时间'].dt.date).agg({col: 'sum' for col in other_columns})
    elif selectbox_value == '每周':
        grouped_df = filtered_df.groupby(filtered_df['时间'].dt.to_period('W')).agg(
            {col: 'sum' for col in other_columns})
    elif selectbox_value == '每月':
        grouped_df = filtered_df.groupby(filtered_df['时间'].dt.to_period('M')).agg(
            {col: 'sum' for col in other_columns})

    grouped_df = grouped_df.reset_index()

    if isinstance(grouped_df.iloc[0, 0], pd.Period):
        grouped_df.iloc[:, 0] = grouped_df.iloc[:, 0].dt.start_time

    return grouped_df

def query_data2(defile, date_range):
    defile['时间'] = pd.to_datetime(defile['时间'])

    if date_range is None or len(date_range) != 2:
        return defile.copy()

    start_date, end_date = date_range
    if not start_date or not end_date:
        raise ValueError("Invalid date range")
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
    mask = (defile['时间'] >= start_date) & (defile['时间'] <= end_date)
    filtered_df = defile.loc[mask]

    if filtered_df.empty:
        return pd.DataFrame()

    filtered_df = filtered_df.reset_index()
    return filtered_df

def yt_stats(df, start_date, end_date):
    # 将时间列转换为 datetime 类型
    df['时间'] = pd.to_datetime(df['时间'])

    # 筛选时间范围内的数据
    df222 = df[(df['时间'] >= start_date) & (df['时间'] <= end_date)]

    # 按意图分组并统计数量
    result = df222.groupby('意图')['数量'].sum().reset_index()
    result = result.sort_values(['数量'], ascending=False)

    # 过滤不需要的行
    exclusions2 = ["转人工服务", "未知意图", "NULL", "", None, "nan"]
    exclusions = ["转人工服务", "儿童疫苗", "语气词", "成人疫苗", "其他问题", "未知意图", "NULL", "", None, "nan"]
    result["意图"] = result["意图"].astype(str)
    result["意图"].replace(np.nan, "NULL", inplace=True)
    name_map = {'疫苗名称-流感疫苗': '疫苗咨询-流感疫苗', '疫苗名称-13价肺炎': '疫苗咨询-13价肺炎',
                '疫苗名称-疱疹疫苗': '疫苗咨询-疱疹疫苗', '疫苗名称-狂犬疫苗': '疫苗咨询-狂犬疫苗',
                '疫苗名称-乙肝疫苗': '疫苗咨询-乙肝疫苗', '疫苗名称-卡介疫苗': '疫苗咨询-卡介疫苗',
                '疫苗名称-脊灰疫苗': '疫苗咨询-脊灰疫苗', '疫苗名称-百白破疫苗': '疫苗咨询-百白破疫苗',
                '疫苗名称-乙脑疫苗': '疫苗咨询-乙脑疫苗', '疫苗名称-流脑疫苗': '疫苗咨询-流脑疫苗',
                '疫苗名称-白破疫苗': '疫苗咨询-白破疫苗', '疫苗名称-麻腮风疫苗': '疫苗咨询-麻腮风疫苗',
                '疫苗名称-甲肝疫苗': '疫苗咨询-甲肝疫苗', '疫苗名称-b型流感疫苗': '疫苗咨询-b型流感疫苗',
                '疫苗名称-水痘疫苗': '疫苗咨询-水痘疫苗', '疫苗名称-轮状疫苗': '疫苗咨询-轮状疫苗',
                '疫苗名称-霍乱疫苗': '疫苗咨询-霍乱疫苗', '疫苗名称-四联疫苗': '疫苗咨询-四联疫苗',
                '疫苗名称-五联疫苗': '疫苗咨询-五联疫苗', '疫苗名称-手足口病疫苗': '疫苗咨询-手足口病疫苗',
                '疫苗名称-23价肺炎': '疫苗咨询-23价肺炎', '疫苗名称-HPV疫苗': '疫苗咨询-HPV疫苗',
                '疫苗名称-二价疫苗': '疫苗咨询-二价疫苗', '儿保科': '儿保科电话', '总值班室': '总值班室电话',
                '新加-ipv补种': '疫苗咨询-ipv补种', '第二针': '疫苗咨询-HPV第二针'}
    result['意图'] = result['意图'].replace(name_map)
    # print(result)
    df_filtered = result[~result["意图"].isin(exclusions)]
    df_filtered = df_filtered[~result["意图"].str.match(r'^-?\d+(\.\d+)?$')]

    return df_filtered

def data_filtering(date_key, filter_date=True):
    df1 =df_sheet3.copy()

    blank, box_date = st.columns([8, 2])
    # 过滤日期
    if filter_date:
        with box_date:
            st.popover('时间').date_input(
                '请选择起止日期', [date(date.today().year, 1, 1), date.today()], key=date_key
            )
        date_range = st.session_state[date_key]
        if len(date_range) != 2:
            date_range = (date(date.today().year, 1, 1), date.today())
        # 筛选时间范围
        start = datetime(date_range[0].year, date_range[0].month, date_range[0].day, 0, 0, 0)
        end = datetime(date_range[1].year, date_range[1].month, date_range[1].day, 23, 59, 59)
        df2 = df1[(df1['时间'] >= start) & (df1['时间'] <= end)]

    if filter_date:
        st.info(f'【当前选择时间范围】：{date_range[0]}~{date_range[1]}')

    filtered_df = df2

    return filtered_df

def render_freq_selectbox(key):
    st.popover("频率").radio(
        '请选择数据变化的时间频率',
        ["日度", "周度", "月度"],
        index=1,
        key=key
    )
    freq = st.session_state[key]

    if freq == '月度':
        freq = 'ME'
    elif freq == '周度':
        freq = 'W-MON'
    elif freq == '日度':
        freq = 'D'

    return freq

def query_detail_fig(filtered_df: pd.DataFrame, freq):
    stats = filtered_df.groupby(pd.Grouper(key='时间', freq=freq)).agg(
        通话时长第1四分位数=('通话时长', lambda x: x.quantile(0.25)),
        通话时长第2四分位数=('通话时长', lambda x: x.quantile(0.75)),
        通话总时长=('通话时长', 'sum'),
        通话平均时长=('通话时长', 'mean'),
        对话轮数第1四分位数=('对话轮数', lambda x: x.quantile(0.25)),
        对话轮数第2四分位数=('对话轮数', lambda x: x.quantile(0.75)),
        对话平均轮数=('对话轮数', 'mean')
    )

    stats['通话时长第1四分位数'] = stats['通话时长第1四分位数'].fillna(0)
    stats['通话时长第2四分位数'] = stats['通话时长第2四分位数'].fillna(0)
    stats['通话平均时长'] = stats['通话平均时长'].fillna(0)
    stats['对话轮数第1四分位数'] = (stats['对话轮数第1四分位数'].fillna(0)).round(2)
    stats['对话轮数第2四分位数'] = (stats['对话轮数第2四分位数'].fillna(0)).round(2)
    stats['对话平均轮数'] = (stats['对话平均轮数'].fillna(0)).round(2)

    # 时长类数据转换为分钟
    stats['通话总时长'] = (stats['通话总时长'] / 60).round(2)
    stats['通话平均时长'] = (stats['通话平均时长'] / 60).round(2)
    stats['通话时长第1四分位数'] = (stats['通话时长第1四分位数'] / 60).round(2)
    stats['通话时长第2四分位数'] = (stats['通话时长第2四分位数'] / 60).round(2)

    # 按freq重置索引
    if freq == 'ME':
        stats.index = stats.index.strftime('%Y-%m')
    elif freq == 'W-MON':
        tmp = pd.DataFrame()
        tmp['周开始日期'] = stats.index
        tmp['周结束日期'] = stats.index + pd.offsets.Week(weekday=6)
        tmp['周范围'] = tmp['周开始日期'].astype('str') + '~' + (tmp['周结束日期']).astype('str')
        stats.index = tmp['周范围']
    elif freq == 'D':
        stats.index = stats.index.strftime('%Y-%m-%d')
    stats.index.name = '时间'

    return stats

def query_detail_fig2(filtered_df: pd.DataFrame, freq):
    stats = filtered_df.groupby(pd.Grouper(key='时间', freq=freq)).agg(
        通话数=('result_id','size')
    )

    stats['通话数'] = stats['通话数'].fillna(0)

    # 按freq重置索引
    if freq == 'ME':
        stats.index = stats.index.strftime('%Y-%m')
    elif freq == 'W-MON':
        tmp = pd.DataFrame()
        tmp['周开始日期'] = stats.index
        tmp['周结束日期'] = stats.index + pd.offsets.Week(weekday=6)
        tmp['周范围'] = tmp['周开始日期'].astype('str') + '~' + (tmp['周结束日期']).astype('str')
        stats.index = tmp['周范围']
    elif freq == 'D':
        stats.index = stats.index.strftime('%Y-%m-%d')
    stats.index.name = '时间'
    stats=stats.sort_values(['时间'], ascending=False)

    return stats


WIDTH3=1400
HEIGHT3=960
def render_calls_detail(data:pd.DataFrame):
    if len(data)==0:
        return

    # 柱形图
    bar=(
        Bar(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH3*0.8}px',height=f'{HEIGHT3*0.4}px'))
        .add_xaxis(data.index.astype('str').tolist())
        .add_yaxis('通话总时长',data['通话总时长'].values.tolist(), label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='#F08080'))
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                axis_pointer_type='cross'
            ),
        )
    )

    # 条形图
    line=(
        Line(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH3*0.8}px',height=f'{HEIGHT3*0.4}px'))
        .add_xaxis(data.index.astype('str').tolist())
        .extend_axis(yaxis=opts.AxisOpts(type_='value',position='right',name='分钟'))
        .add_yaxis('通话平均时长',data['通话平均时长'], label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='green'),yaxis_index=1,color='green')
        .add_yaxis('通话时长上四分位数',data['通话时长第1四分位数'], label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='blue'),yaxis_index=1,color='red')
        .add_yaxis('通话时长下四分位数', data['通话时长第2四分位数'], label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='orange'), yaxis_index=1, color='red')
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                axis_pointer_type='cross',
            ),
            datazoom_opts=opts.DataZoomOpts(),
            # title_opts=opts.TitleOpts(title='通话时长图'),
            title_opts=opts.TitleOpts(title="通话时长详情", subtitle="分钟"),
            legend_opts=opts.LegendOpts(type_='scroll')
        )
    )
    # 组合绘图
    grid_html=line.overlap(bar)
    components.html(grid_html.render_embed(),width=WIDTH3*0.8,height=HEIGHT3*0.4)

def render_calls_detail2(data:pd.DataFrame):
    if len(data)==0:
        return

    # 折线图
    line=(
        Line(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH3*0.8}px',height=f'{HEIGHT3*0.4}px'))
        .add_xaxis(data.index.astype('str').tolist())
        .extend_axis(yaxis=opts.AxisOpts(type_='value',position='left',name='轮数'))
        .add_yaxis('对话平均轮数',data['对话平均轮数'], label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='green'),yaxis_index=1,color='green')
        .add_yaxis('对话轮数上四分位数',data['对话轮数第1四分位数'], label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='blue'),yaxis_index=1,color='red')
        .add_yaxis('对话轮数下四分位数', data['对话轮数第2四分位数'], label_opts=opts.LabelOpts(is_show=False), itemstyle_opts = opts.ItemStyleOpts(color='orange'), yaxis_index=1, color='red')
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                axis_pointer_type='cross',
            ),
            datazoom_opts=opts.DataZoomOpts(),
            title_opts=opts.TitleOpts(title='对话轮数详情'),
            # title_opts=opts.TitleOpts(title="对话轮数详情", subtitle="分钟"),
            legend_opts=opts.LegendOpts(type_='scroll')
        )
    )
    components.html(line.render_embed(),width=WIDTH3*0.8,height=HEIGHT3*0.4)


render_header_and_date_selector_organization("数据总览", [], "select_box_organization", "date_input1")

select_box_organization = st.session_state["select_box_organization"]
date_input1 = st.session_state["date_input1"]

total_df = query_data(df, date_input1)

col1, col2 = st.columns([1, 3])

try:
    total_calls = total_df["通话数"].sum()
    total_conversations = total_df["对话数"].sum()
except KeyError:
    total_calls = 0
    total_conversations = 0

with col1:
    st.markdown(f'''
        <div class="metric-container">
            <div class="data-title">
                <span style="font-size: 1.5rem;">通话总数</span>
                 <span class="icon-container">
                    <span class="icon">!</span>
                </span>
            </div>
            <div style="height:50px;line-height: 50px;">
                <span style="font-size: 2.5rem; font-weight: bold;">{total_calls}</span>
                <span style="font-size: 1.5rem; font-weight: bold;">个</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''
        <div class="metric-container">
            <div class="data-title">
                <span style="font-size: 1.5rem;">对话数</span>
                 <span class="icon-container">
                    <span class="icon">!</span>
                </span>
            </div>
            <div style="height:50px;line-height: 50px;">
                <span style="font-size: 2.5rem; font-weight: bold;">{total_conversations}</span>
                <span style="font-size: 1.5rem; font-weight: bold;">次</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)

render_header_and_date_selector("对话统计详情", [], "select_box2",
                                "date_input2")

select_box2 = st.session_state["select_box2"]
date_input2 = st.session_state["date_input2"]

total_detail_df = query_data(df, date_input2)
QRV_df5 = query_data2(df_sheet3, date_input2)

try:
    avg_call_duration = round(total_detail_df["平均通话时长"].mean() / 60, 3)
    avg_conversation_rounds = round(total_detail_df["平均对话轮数"].mean(), 3)
    avg_daily_service_calls = round(total_detail_df["通话数"].mean(), 3)
except KeyError:
    avg_call_duration = 0
    avg_conversation_rounds = 0
    avg_daily_service_calls = 0

st.markdown(f'''
    <div class="metric-container topic">
        <div class="column">
            <div class="metric">
                <span class="metric-title">
                    <span style="font-size: 1.5rem;">平均通话时长</span>
                    <span class="icon-container">
                        <span class="icon">!</span>
                    </span>
                 </span>
                <div class="metric-value">
                    <div class="value">
                        <span>{avg_call_duration}</span>
                        <span>分钟</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="column">
            <div class="metric">
                <span class="metric-title">
                    <span style="font-size: 1.5rem;">平均对话轮数</span>
                    <span class="icon-container">
                        <span class="icon">!</span>
                    </span>
                </span>
                <span class="metric-value">
                    <div>
                        <span>{avg_conversation_rounds}</span>
                        <span>轮</span>
                    </div>
                </span>
            </div>
        </div>
        <div class="column">
            <div class="metric">
                <span class="metric-title">
                    <span style="font-size: 1.5rem;">日平均服务通话数</span>
                    <span class="icon-container">
                        <span class="icon">!</span>
                    </span>
                </span>
                <span class="metric-value">
                    <div>
                        <span>{avg_daily_service_calls}</span>
                        <span>通</span>
                    </div>
                </span>
            </div>
        </div>
    </div>
''', unsafe_allow_html=True)

def clean_percentage_column(df, column_name):
    if column_name in df.columns:
        df[column_name] = df[column_name].replace('%', '', regex=True).astype(float) / 100
    return df


# 绘制柱状图-平均通话时长
fig1, ax = plt.subplots(figsize=(10, 5))

if '时间' not in total_detail_df.columns or total_detail_df.empty:
    resampled_df = pd.DataFrame(columns=['时间', '平均通话时长'])
else:
    total_detail_df['时间'] = pd.to_datetime(total_detail_df['时间'])
    total_detail_df = clean_percentage_column(total_detail_df, '通话时长')
    total_detail_df['平均通话时长'] = total_detail_df['平均通话时长'] / 60

    if select_box2 == "每日":
        resampled_df = total_detail_df.set_index('时间').resample('D')['平均通话时长'].mean().reset_index()
    elif select_box2 == "每周":
        resampled_df = total_detail_df.set_index('时间').resample('W')['平均通话时长'].mean().reset_index()
    elif select_box2 == "每月":
        resampled_df = total_detail_df.set_index('时间').resample('M')['平均通话时长'].mean().reset_index()
    elif select_box2 == "每年":
        resampled_df = total_detail_df.set_index('时间').resample('Y')['平均通话时长'].mean().reset_index()

time = resampled_df['时间']
avg_call_length = resampled_df['平均通话时长']

width = 0.6

# 绘制柱状图-平均通话时长
ax.bar(time, avg_call_length, color='lightblue', width=width)

# 绘制折线图-平均通话时长
ax.plot(time, avg_call_length, marker='o', linestyle='-', color='b')

# 设置标题和标签-平均通话时长
# ax.set_title("平均通话时长变化", fontsize=16)
ax.grid(True)
ax.legend()


# 绘制柱状图-平均对话轮数
fig2, ax2 = plt.subplots(figsize=(10, 5))

if '平均对话轮数' in total_detail_df.columns:
    total_detail_df['平均对话轮数'] = total_detail_df['平均对话轮数'].replace('%', '', regex=True).astype(float)
    if select_box2 == "每日":
        resampled_df2 = total_detail_df.set_index('时间').resample('D')['平均对话轮数'].mean().reset_index()
    elif select_box2 == "每周":
        resampled_df2 = total_detail_df.set_index('时间').resample('W')['平均对话轮数'].mean().reset_index()
    elif select_box2 == "每月":
        resampled_df2 = total_detail_df.set_index('时间').resample('M')['平均对话轮数'].mean().reset_index()
    elif select_box2 == "每年":
        resampled_df2 = total_detail_df.set_index('时间').resample('Y')['平均对话轮数'].mean().reset_index()

    time2 = resampled_df2['时间']
    avg_conversation_rounds = resampled_df2['平均对话轮数']

    # 绘制柱状图-平均对话轮数
    ax2.bar(time2, avg_conversation_rounds, color='lightgreen', width=width)

    # 绘制折线图-平均对话轮数
    ax2.plot(time2, avg_conversation_rounds, marker='o', linestyle='-', color='g')

    # 设置标题和标签-平均对话轮数
    # ax2.set_title("平均对话轮数变化", fontsize=16)
    ax2.grid(True)
    ax2.legend()

# 绘制柱状图-日平均服务通话数
fig3, ax3 = plt.subplots(figsize=(10, 5))

if '通话数' in total_detail_df.columns:
    if select_box2 == "每日":
        resampled_df3 = total_detail_df.set_index('时间').resample('D')['通话数'].mean().reset_index()
    elif select_box2 == "每周":
        resampled_df3 = total_detail_df.set_index('时间').resample('W')['通话数'].mean().reset_index()
    elif select_box2 == "每月":
        resampled_df3 = total_detail_df.set_index('时间').resample('M')['通话数'].mean().reset_index()
    elif select_box2 == "每年":
        resampled_df3 = total_detail_df.set_index('时间').resample('Y')['通话数'].mean().reset_index()

    time3 = resampled_df3['时间']
    avg_daily_service_calls = resampled_df3['通话数']

    # 绘制柱状图-日平均服务通话数
    ax3.bar(time3, avg_daily_service_calls, color='lightcoral', width=width)

    # 绘制折线图-日平均服务通话数
    ax3.plot(time3, avg_daily_service_calls, marker='o', linestyle='-', color='r')

    # 设置标题和标签-日平均服务通话数
    # ax3.set_title("日平均服务通话数变化", fontsize=16)
    ax3.grid(True)
    ax3.legend()

col1_detail, col2_detail, col3_detail = st.columns([1, 1, 1])

with col1_detail:
    with st.expander("查看详情 - 平均通话时长"):
        # st.markdown('<div class="subheader">平均通话时长变化</div>', unsafe_allow_html=True)
        st.pyplot(fig1)
with col2_detail:
    with st.expander("查看详情 - 平均对话轮数"):
        st.pyplot(fig2)
with col3_detail:
    with st.expander("查看详情 - 日平均服务通话数"):
        st.pyplot(fig3)

with st.container(border=True):
    # 2个子页面
    tab_calls, tab_duration = st.tabs(["通话时长详情", "对话轮数详情"])
    with tab_calls:
        freq2 = render_freq_selectbox('detail')
        render_calls_detail(query_detail_fig(QRV_df5, freq2))
    with tab_duration:
        freq2 = render_freq_selectbox('detail2')
        render_calls_detail2(query_detail_fig(QRV_df5, freq2))


# QRV转人工趋势
render_header_and_date_selector("QRV转人工趋势", [],
                                "select_box3", "date_input3")

select_box3 = st.session_state["select_box3"]
date_input3 = st.session_state["date_input3"]

QRV_df = query_data(df, date_input3)


def clean_percentage(col):
    return col.str.rstrip('%').astype('float') / 100.0


try:
    # 清理和转换百分比列
    QRV_df['直接转人工率'] = clean_percentage(QRV_df['直接转人工率'])
    QRV_df['咨询后转人工率'] = clean_percentage(QRV_df['咨询后转人工率'])
    QRV_df['时间'] = pd.to_datetime(QRV_df['时间'])

    # 按月份分组并统计
    if select_box3 == "每日":
        grouped_stats = QRV_df.resample('D', on='时间').agg({
            '直接转人工率': 'mean',
            '咨询后转人工率': 'mean',
            '通话数': 'sum',
            '对话数': 'sum'
        }).reset_index()
    elif select_box3 == "每周":
        grouped_stats = QRV_df.resample('W', on='时间').agg({
            '直接转人工率': 'mean',
            '咨询后转人工率': 'mean',
            '通话数': 'sum',
            '对话数': 'sum'
        }).reset_index()
    elif select_box3 == "每月":
        grouped_stats = QRV_df.resample('M', on='时间').agg({
            '直接转人工率': 'mean',
            '咨询后转人工率': 'mean',
            '通话数': 'sum',
            '对话数': 'sum'
        }).reset_index()

    # 转换月份为字符串
    grouped_stats['时间'] = grouped_stats['时间'].astype(str)

    months = grouped_stats['时间']
    calls = grouped_stats['通话数']
    chats = grouped_stats['对话数']
    direct_rate = grouped_stats['直接转人工率']
    consult_rate = grouped_stats['咨询后转人工率']
except KeyError:
    months = []
    calls = []
    chats = []
    direct_rate = []
    consult_rate = []

if len(months) > 0:
    x = np.arange(len(months))  # 月份的位置
    width = 0.35  # 柱状图的宽度
    WIDTH = 1000
    HEIGHT = 1440

    # 柱形图
    bar = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND, width=f'{WIDTH * 0.8}px', height=f'{HEIGHT * 0.4}px'))
        .add_xaxis(months.tolist())
        .add_yaxis('通话数', calls.tolist(), itemstyle_opts=opts.ItemStyleOpts(color='blue'), label_opts=opts.LabelOpts(is_show=False))
        .add_yaxis('对话数', chats.tolist(), itemstyle_opts=opts.ItemStyleOpts(color='orange'), label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                axis_pointer_type='cross'
            ),
            datazoom_opts=opts.DataZoomOpts()
        )
    )
    # 渲染图表为 HTML
    bar_html = bar.render_embed()

    # 折线图
    direct_rate_percentage = [value * 100 for value in direct_rate]
    consult_rate_percentage = [value * 100 for value in consult_rate]
    line = (
        Line(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND, width=f'{WIDTH * 0.8}px', height=f'{HEIGHT * 0.4}px'))
        .add_xaxis(months.tolist())
        .extend_axis(yaxis=opts.AxisOpts(type_='value', position='right', name='百分比', axislabel_opts=opts.LabelOpts(formatter="{value}%")))
        .add_yaxis('直接转人工率', direct_rate_percentage, itemstyle_opts=opts.ItemStyleOpts(color='blue'), label_opts=opts.LabelOpts(is_show=False), yaxis_index=1, color='green')
        .add_yaxis('咨询后转人工率', consult_rate_percentage, itemstyle_opts=opts.ItemStyleOpts(color='orange'), label_opts=opts.LabelOpts(is_show=False), yaxis_index=1, color='red')
        .set_global_opts(
            tooltip_opts=opts.TooltipOpts(
                trigger='axis',
                axis_pointer_type='cross',
            ),
            datazoom_opts=opts.DataZoomOpts(),
            # title_opts=opts.TitleOpts(title='通话人次变化曲线'),
            legend_opts=opts.LegendOpts(type_='scroll')
        )
    )
    # 渲染图表为 HTML
    line_html = line.render_embed()

    with st.container():
        col11, col12 = st.columns(2)
        with col11:
            st.components.v1.html(bar_html,width=WIDTH*0.8, height=HEIGHT*0.4)
        with col12:
            st.components.v1.html(line_html, width=WIDTH * 0.8, height=HEIGHT * 0.4)

# TOP分类标签
# QRV转人工趋势
render_header_and_date_selector_organization("TOP15分类标签", [], "select_box4", "date_input4")

select_box4 = st.session_state["select_box4"]
date_input4 = st.session_state["date_input4"]

if len(date_input4) == 2:
    start_date2, end_date2 = date_input4
    start_date2 = pd.Timestamp(start_date2)
    end_date2 = pd.Timestamp(end_date2)
else:
    today = date.today()
    thirty_one_days_ago = today - timedelta(days=31)
    start_date2 = pd.Timestamp(thirty_one_days_ago)
    end_date2 = pd.Timestamp(today)

df_filtered = yt_stats(df_sheet2, start_date2, end_date2)

total_quantity = df_filtered["数量"].sum()

# 计算数量前10项的占比
top_tags = df_filtered.nlargest(15, "数量").copy()
top_tags["占比"] = top_tags["数量"]

# 20240820版条形图
top_tags_sorted = top_tags.sort_values(by='占比', ascending=True)
bar1 = (
    Bar(init_opts=opts.InitOpts(width=f'{1400*0.6}px',height=f'{960*0.6}px'))
    .add_xaxis(top_tags_sorted['意图'].values.tolist())
    .add_yaxis("", top_tags_sorted['占比'].values.tolist(),
               itemstyle_opts=opts.ItemStyleOpts(color="#F4A460"))
    .reversal_axis()
    .set_series_opts(label_opts=opts.LabelOpts(position="right"))
    .set_global_opts(
                     # title_opts=opts.TitleOpts(title="Bar-翻转 XY 轴"),
                     xaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=False)),
                     yaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=False),
                                              axislabel_opts=opts.LabelOpts(rotate=45))
                     )
)

# # 老版条形图
# fig, ax1 = plt.subplots(figsize=(10, 6))
#
# # 绘制数量条形图
# sns.barplot(
#     x='数量',
#     y='意图',
#     data=top_tags,
#     palette='Set2',
#     ax=ax1
# )
#
# # 添加占比文本
# for i, (value, pct) in enumerate(zip(top_tags["数量"], top_tags["占比"])):
#     # ax1.text(value, i, f'{pct:.0f}%', color='black', va='center')
#     ax1.text(value, i, pct, color='black', va='center')
#
# # 设置X轴标签
# ax1.set_xlabel('数量')
# ax1.set_ylabel('')
#
# sns.despine(left=True, bottom=True)
# # 老版条形图

# 生成词云图数据
words = df_filtered["意图"].tolist()
word_counts = df_filtered["数量"].tolist()
wordcloud_data = [(word, count) for word, count in zip(words, word_counts)]
print(wordcloud_data)

# 创建词云图
wordcloud = WordCloud()
wordcloud.add("", wordcloud_data, word_size_range=[10, 70], shape="circle")
wordcloud.set_global_opts(title_opts=opts.TitleOpts(title="词云图"))

# 显示结果
with st.container():
    col6, col7 = st.columns(2)

    # 条形图
    with col6:
        # st.pyplot(fig)
        st.components.v1.html(bar1.render_embed(), width=1400 * 0.6, height=960 * 0.6)

    # 词云图
    with col7:
        wordcloud.set_global_opts(
            title_opts=opts.TitleOpts(title="词云图"),
            # visualmap_opts=opts.VisualMapOpts(max_=200)
            visualmap_opts=opts.VisualMapOpts()
        )
        st_pyecharts(wordcloud, height="503px")

# 原始数据
# st.write(top_tags)

# 月度数据对比
render_header_and_date_selector("月度数据对比", [],
                                "select_box5", "date_input5", show_selectbox=False)

# select_box5 = st.session_state["select_box5"]
date_input5 = st.session_state["date_input5"]

QRV_df2 = query_data(df, date_input5)
try:
    QRV_df2['时间'] = pd.to_datetime(QRV_df2['时间'])
    grouped_stats2 = QRV_df2.resample('M', on='时间').agg({
        '通话数': 'sum',
        '对话数': 'sum'
    }).reset_index()

    # 转换月份为字符串
    grouped_stats2['时间'] = grouped_stats2['时间'].dt.strftime('%Y-%m')
    grouped_stats2['时间'] = grouped_stats2['时间'].astype(str)

    months = grouped_stats2['时间']
    calls = grouped_stats2['通话数']
    chats = grouped_stats2['对话数']
except KeyError:
    months = []
    calls = []
    chats = []

WIDTH=1400
HEIGHT=960
print(months)
picbar=PictorialBar(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.6}px',height=f'{HEIGHT*0.6}px'))
picbar.add_xaxis(months.tolist())
picbar.add_yaxis(
        '对话数',
        chats.tolist(),
        label_opts=opts.LabelOpts(is_show=False, position="right"),
        symbol_size=18,symbol_repeat='fixed',is_symbol_clip=True,symbol=symbols["chat"], # symbol=SymbolType.DIAMOND
        symbol_offset=[0,15]
    )
picbar.add_yaxis(
        '通话数',
        calls.tolist(),
        label_opts=opts.LabelOpts(is_show=False, position="right"),
        symbol_size=18,symbol_repeat='fixed',is_symbol_clip=True,symbol=symbols["phone"], # symbol=SymbolType.ROUND_RECT
        symbol_offset=[0,-15],  # 调整数据点位置
    )
picbar.reversal_axis()
# picbar.set_series_opts(label_opts=opts.LabelOpts(position="right"))
picbar.set_global_opts(
        # title_opts=opts.TitleOpts(title='月呼出人次与成功率'),
        xaxis_opts=opts.AxisOpts(is_show=True),
        yaxis_opts=opts.AxisOpts(
            axistick_opts=opts.AxisTickOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(opacity=0)),
            # axislabel_opts=opts.LabelOpts(margin=15)  # 调整标签间距
        ),
        legend_opts=opts.LegendOpts(pos_top='bottom')
    )

# st.components.v1.html(picbar.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)

# 3个月分时段统计表
# 获取当前日期
today2 = datetime.now()
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
current_month_start = today.replace(day=1)
current_month_end = today2
previous_month_end = current_month_start - timedelta(days=1)
previous_month_start = previous_month_end.replace(day=1)
previous_month_end = previous_month_end.replace(hour=23, minute=59, second=59, microsecond=0)
last_month_end = previous_month_start - timedelta(days=1)
last_month_start = last_month_end.replace(day=1)
last_month_end = last_month_end.replace(hour=23, minute=59, second=59, microsecond=0)

# 定义时间范围
date_ranges = {
    '当前月': (current_month_start, current_month_end),
    '上个月': (previous_month_start, previous_month_end),
    '上上个月': (last_month_start, last_month_end),
}

def compute_hourly_stats(df, start_date, end_date):
    # 将时间列转换为 datetime 类型
    df['时间'] = pd.to_datetime(df['时间'])

    # 筛选时间范围内的数据
    filtered_df = df[(df['时间'] >= start_date) & (df['时间'] <= end_date)]

    # 提取小时
    filtered_df['hour'] = filtered_df['时间'].dt.hour

    # 统计每小时的数量和转人工服务的数量
    hourly_stats = filtered_df.groupby('hour').agg(
        quantity=('hour', 'size'),
        transfer_count=('aa', lambda x: (x.str.contains('转人工服务') & (x != '转人工服务')).sum())
    ).reset_index()

    # 计算转人工率
    hourly_stats['转人工率'] = hourly_stats['transfer_count'] / hourly_stats['quantity']

    # 重命名列
    hourly_stats = hourly_stats.rename(columns={
        'hour': '小时',
        'quantity': '通话数',
    })

    data = hourly_stats[['小时', '通话数', '转人工率']]

    return data

data2 = compute_hourly_stats(df_sheet3, current_month_start, current_month_end)
data3 = compute_hourly_stats(df_sheet3, previous_month_start, previous_month_end)
data4 = compute_hourly_stats(df_sheet3, last_month_start, last_month_end)

style={
'小时':'{0}:00 ~ {0}:59',
'转人工率':'{0:.2%}'
}
# table=data2.style.format(style).background_gradient(subset=['通话数'],cmap='Greens').highlight_max(subset=['转人工率'],props='background-color:pink')
table2=data2.style.format(style).background_gradient(subset=['通话数'],cmap='Reds')
table3=data3.style.format(style).background_gradient(subset=['通话数'],cmap='Reds')
table4=data4.style.format(style).background_gradient(subset=['通话数'],cmap='Reds')

# 用户粘性表
QRV_df3 = query_data2(df_sheet3, date_input5)
# print(QRV_df3)

# 找出最大值和最小值
min_time = QRV_df3['时间'].min()
max_time = QRV_df3['时间'].max()

# 统计每个call_number的总数
count_series = QRV_df3['call_number'].value_counts()
# 只保留大于1的记录
filtered_count = count_series[count_series > 1]
# 格式化call_number，4-7位加*
def format_number(num):
    num_str = str(num)
    return num_str[:3] + '*' * 4 + num_str[7:]

# 应用格式化函数
formatted_numbers = filtered_count.index.to_series().apply(format_number)

# 创建新的DataFrame
result_df = pd.DataFrame({
    'call_number2': formatted_numbers,
    'count': filtered_count.values
})

# 显示结果
table5=result_df[['call_number2','count']]
# 重命名列
table5 = table5.rename(columns={
    'call_number2': '手机号',
    'count': '拨打次数',
})
table5=table5.style.background_gradient(subset=['拨打次数'],cmap='Greens')

with st.container():
    # col13, col14, col15 = st.columns([1.6, 0.8, 0.5])
    col13, col14 = st.columns([2, 1])
    with col13:
        st.components.v1.html(picbar.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)
    with col14:
        st.write(f'{current_month_start.month}月(截止{today.date()})分时段统计')
        st.dataframe(table2, width=int(WIDTH * 0.3), height=int(HEIGHT * 0.15), hide_index=True)
        st.write(f'{previous_month_start.month}月分时段统计')
        st.dataframe(table3, width=int(WIDTH * 0.3), height=int(HEIGHT * 0.15), hide_index=True)
        st.write(f'{last_month_start.month}月分时段统计')
        st.dataframe(table4, width=int(WIDTH * 0.3), height=int(HEIGHT * 0.15), hide_index=True)


# 近3个月意图分类图
data22 = yt_stats(df_sheet2, current_month_start, current_month_end)
data23 = yt_stats(df_sheet2, previous_month_start, previous_month_end)
data24 = yt_stats(df_sheet2, last_month_start, last_month_end)

total22 = data22["数量"].sum()
top_tags22 = data22.nlargest(15, "数量").copy()
top_tags22["占比"] = round(top_tags22["数量"] / total22 * 100,2)

total23 = data23["数量"].sum()
top_tags23 = data23.nlargest(15, "数量").copy()
top_tags23["占比"] = round(top_tags23["数量"] / total23 * 100,2)

total24= data24["数量"].sum()
top_tags24 = data24.nlargest(15, "数量").copy()
top_tags24["占比"] = round(top_tags24["数量"] / total24 * 100,2)


pie1=(
    Pie(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.3}px',height=f'{HEIGHT*0.35}px'))
    .add(
        '',[list(z) for z in zip(top_tags22["意图"].values.tolist(),top_tags22['占比'].values.tolist())],
        radius=['30%','75%'],
        label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c}%")
    )
    .set_colors(['#4682B4','#4169E1','#7B68EE','#FF4500','#F4A460','#F0E68C','#87CEFA','#708090','#66CDAA','#1E90FF','#00FA9A', '#FF00FF', '#FFFACD', '#D8BFD8', '#B0C4DE'])
    .set_global_opts(
        legend_opts=opts.LegendOpts(type_='scroll',pos_top='bottom'),
        # title_opts=opts.TitleOpts(title=f'{current_month_start.month}月意图TOP15')
    )
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}%"))
)
# pie_html1 = pie.render_embed()  # 使用 render_embed() 而不是 render()

pie2=(
    Pie(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.3}px',height=f'{HEIGHT*0.35}px'))
    .add(
        '',[list(z) for z in zip(top_tags23["意图"].values.tolist(),top_tags23['占比'].values.tolist())],
        radius=['30%','75%'],
        label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c}%")
    )
    .set_colors(['#4682B4','#4169E1','#7B68EE','#FF4500','#F4A460','#F0E68C','#87CEFA','#708090','#66CDAA','#1E90FF','#00FA9A', '#FF00FF', '#FFFACD', '#D8BFD8', '#B0C4DE'])
    .set_global_opts(
        legend_opts=opts.LegendOpts(type_='scroll',pos_top='bottom'),
        # title_opts=opts.TitleOpts(title=f'{current_month_start.month}月意图TOP15')
    )
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}%"))
)

pie3=(
    Pie(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.3}px',height=f'{HEIGHT*0.35}px'))
    .add(
        '',[list(z) for z in zip(top_tags24["意图"].values.tolist(),top_tags24['占比'].values.tolist())],
        radius=['30%','75%'],
        label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c}%")
    )
    .set_colors(['#4682B4','#4169E1','#7B68EE','#FF4500','#F4A460','#F0E68C','#87CEFA','#708090','#66CDAA','#1E90FF','#00FA9A', '#FF00FF', '#FFFACD', '#D8BFD8', '#B0C4DE'])
    .set_global_opts(
        legend_opts=opts.LegendOpts(type_='scroll',pos_top='bottom'),
        # title_opts=opts.TitleOpts(title=f'{current_month_start.month}月意图TOP15')
    )
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}%"))
)

# 近3周意图分类图
def get_monday(date):
    """返回给定日期所在周的周一的日期"""
    # 计算周一与给定日期之间的天数差
    # days_to_monday = (7 - date.weekday()) % 7
    days_to_monday = (date.weekday()) % 7
    return date - timedelta(days=days_to_monday)


def get_sunday(date):
    """返回给定日期所在周的周日的日期"""
    # 计算周日与给定日期之间的天数差
    days_to_sunday = 6 - date.weekday()
    return date + timedelta(days=days_to_sunday)


# 获取今天的日期
# today2 = datetime.now()

# 本周的周一和周日
this_week_monday = get_monday(today)
this_week_sunday = get_sunday(today)
this_week_sunday = this_week_sunday.replace(hour=23, minute=59, second=59, microsecond=0)
# 上周的周一和周日
last_week_monday = this_week_monday - timedelta(weeks=1)
last_week_sunday = this_week_sunday - timedelta(weeks=1)
# 上上周的周一和周日
two_weeks_ago_monday = last_week_monday - timedelta(weeks=1)
two_weeks_ago_sunday = last_week_sunday - timedelta(weeks=1)

data25 = yt_stats(df_sheet2, this_week_monday, today2)
data26 = yt_stats(df_sheet2, last_week_monday, last_week_sunday)
data27 = yt_stats(df_sheet2, two_weeks_ago_monday, two_weeks_ago_sunday)

total25 = data25["数量"].sum()
top_tags25 = data25.nlargest(10, "数量").copy()
top_tags25["占比"] = round(top_tags25["数量"] / total25 * 100,2)

total26 = data26["数量"].sum()
top_tags26 = data26.nlargest(10, "数量").copy()
top_tags26["占比"] = round(top_tags26["数量"] / total26 * 100,2)

total27= data27["数量"].sum()
top_tags27 = data27.nlargest(10, "数量").copy()
top_tags27["占比"] = round(top_tags27["数量"] / total27 * 100,2)

pie4=(
    Pie(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.3}px',height=f'{HEIGHT*0.35}px'))
    .add(
        '',[list(z) for z in zip(top_tags25["意图"].values.tolist(),top_tags25['占比'].values.tolist())],
        # radius=['30%','75%'],
        # center=["50%", "60%"],
        rosetype="area",
        label_opts=opts.LabelOpts(is_show=False, formatter="{b}: {c}%")
    )
    .set_colors(['#4682B4','#4169E1','#7B68EE','#FF4500','#F4A460','#F0E68C','#87CEFA','#708090','#66CDAA','#1E90FF','#00FA9A', '#FF00FF', '#FFFACD', '#D8BFD8', '#B0C4DE'])
    .set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='scroll',pos_top='bottom'),
        # title_opts=opts.TitleOpts(title=f'{current_month_start.month}月意图TOP15')
    )
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True,formatter="{b}: {c}%"))
)

pie5=(
    Pie(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.3}px',height=f'{HEIGHT*0.35}px'))
    .add(
        '',[list(z) for z in zip(top_tags26["意图"].values.tolist(),top_tags26['占比'].values.tolist())],
        # radius=['30%','75%'],
        # center=["50%", "60%"],
        rosetype="area",
        label_opts=opts.LabelOpts(is_show=False, formatter="{b}: {c}%")
    )
    .set_colors(['#4682B4','#4169E1','#7B68EE','#FF4500','#F4A460','#F0E68C','#87CEFA','#708090','#66CDAA','#1E90FF','#00FA9A', '#FF00FF', '#FFFACD', '#D8BFD8', '#B0C4DE'])
    .set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='scroll',pos_top='bottom'),
        # title_opts=opts.TitleOpts(title=f'{current_month_start.month}月意图TOP15')
    )
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True,formatter="{b}: {c}%"))
)

pie6=(
    Pie(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND,width=f'{WIDTH*0.3}px',height=f'{HEIGHT*0.35}px'))
    .add(
        '',[list(z) for z in zip(top_tags27["意图"].values.tolist(),top_tags27['占比'].values.tolist())],
        # radius=['30%','75%'],
        # center=["50%", "60%"],
        rosetype="area",
        label_opts=opts.LabelOpts(is_show=False, formatter="{b}: {c}%")
    )
    .set_colors(['#4682B4','#4169E1','#7B68EE','#FF4500','#F4A460','#F0E68C','#87CEFA','#708090','#66CDAA','#1E90FF','#00FA9A', '#FF00FF', '#FFFACD', '#D8BFD8', '#B0C4DE'])
    .set_global_opts(
        legend_opts=opts.LegendOpts(is_show=True, type_='scroll',pos_top='bottom'),
        # title_opts=opts.TitleOpts(title=f'{current_month_start.month}月意图TOP15')
    )
    .set_series_opts(label_opts=opts.LabelOpts(is_show=True,formatter="{b}: {c}%"))
)

with st.container(border=True):
    # st.subheader("变化曲线")
    # 2个子页面
    tab_calls,tab_duration=st.tabs(["近3个月","近3周"])
    with tab_calls:
        col15, col16, col17 = st.columns(3)
        with col15:
            html_content4 = f'<strong><span style="font-size: 24px;">{current_month_start.month}月(截止{today.date()})意图TOP15</span></strong>'
            # 在Streamlit中显示HTML内容
            st.write(html_content4, unsafe_allow_html=True)
            # st.write(f'{current_month_start.month}月意图TOP15')
            st.components.v1.html(pie1.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)
        with col16:
            html_content5 = f'<strong><span style="font-size: 24px;">{previous_month_start.month}月意图TOP15</span></strong>'
            # 在Streamlit中显示HTML内容
            st.write(html_content5, unsafe_allow_html=True)
            # st.write(f'{previous_month_start.month}月意图TOP15')
            st.components.v1.html(pie2.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)
        with col17:
            html_content6 = f'<strong><span style="font-size: 24px;">{last_month_start.month}月意图TOP15</span></strong>'
            # 在Streamlit中显示HTML内容
            st.write(html_content6, unsafe_allow_html=True)
            # st.write(f'{last_month_start.month}月意图TOP15')
            st.components.v1.html(pie3.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)
with tab_duration:
        col18,col19,col20=st.columns(3)
        with col18:
            html_content1 = f'<strong><span style="font-size: 24px;">{this_week_monday.date()}至{today2.date()} 意图TOP10</span></strong>'
            # 在Streamlit中显示HTML内容
            st.write(html_content1, unsafe_allow_html=True)
            # st.write(f'{this_week_monday.date()}至{today2.date()}意图TOP10')
            st.components.v1.html(pie4.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)
        with col19:
            html_content2 = f'<strong><span style="font-size: 24px;">{last_week_monday.date()}至{last_week_sunday.date()} 意图TOP10</span></strong>'
            # 在Streamlit中显示HTML内容
            st.write(html_content2, unsafe_allow_html=True)
            # st.write(f'{last_week_monday.date()}至{last_week_sunday.date()}意图TOP10')
            st.components.v1.html(pie5.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)
        with col20:
            # 使用HTML标签来加粗和改变字号
            html_content3 = f'<strong><span style="font-size: 24px;">{two_weeks_ago_monday.date()}至{two_weeks_ago_sunday.date()} 意图TOP10</span></strong>'
            # 在Streamlit中显示HTML内容
            st.write(html_content3, unsafe_allow_html=True)
            # st.write(f'{two_weeks_ago_monday.date()}至{two_weeks_ago_sunday.date()}意图TOP10')
            st.components.v1.html(pie6.render_embed(),width=WIDTH*0.6, height=HEIGHT*0.6)

# 呼入归属地map
render_header_and_date_selector("用户分析", [],
                                "select_box6", "date_input6", show_selectbox=False)

date_input6 = st.session_state["date_input6"]
QRV_df4 = query_data2(df_sheet3, date_input6)
min_t = QRV_df4['时间'].min()
max_t = QRV_df4['时间'].max()

# 初始化Phone对象
p = Phone()
# 创建一个新的DataFrame来存储归属地信息
df_location = pd.DataFrame(columns=['call_number', 'province', 'city'])

# 查询每个手机号的归属地并存储结果
for index, row in QRV_df4.iterrows():
    tel = row['call_number']
    location_info = p.find(tel)
    if location_info:  # 确保find方法返回了结果
        df_location = df_location._append({
            'call_number': tel,
            'province': location_info['province'],
            'city': location_info['city']
        }, ignore_index=True)

# 按province统计数量
province_counts = df_location.groupby('province').size()
# 将结果存储为DataFrame（如果需要索引作为列）
province_counts_df = province_counts.reset_index(name='count')

# 定义一个函数来修改province的值
def modify_province(province):
    if province in ['北京', '天津', '上海', '重庆']:
        return province + '市'
    elif province in ['内蒙古', '西藏']:
        return province + '自治区'
    elif province == '广西':
        return province + '壮族自治区'
    elif province == '宁夏':
        return province + '回族自治区'
    elif province == '新疆':
        return province + '维吾尔自治区'
    else:
        return province + '省'


# 使用apply函数和lambda表达式来应用修改函数
province_counts_df['province'] = province_counts_df['province'].apply(lambda x: modify_province(x))

# 2. 当province为浙江时，按city统计数量
zhejiang_city_counts = df_location[df_location['province'] == '浙江'].groupby('city').size()
zhejiang_city_counts_df = zhejiang_city_counts.reset_index(name='count')
zhejiang_city_counts_df['city'] = zhejiang_city_counts_df['city'] + '市'
# print(zhejiang_city_counts_df)

c1 = (
    Map()
    .add('', [list(z) for z in zip(zhejiang_city_counts_df['city'].values.tolist(), zhejiang_city_counts_df['count'].values.tolist())], "浙江",
         label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c}")
         )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="浙江省"),
        visualmap_opts=opts.VisualMapOpts()
    )
    # .render("map_guangdong.html")
)
# st.components.v1.html(c1.render_embed(), height=600)

c2 = (
    Map()
    .add('', [list(z) for z in zip(province_counts_df['province'].values.tolist(), province_counts_df['count'].values.tolist())], "china",
         label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c}")
         )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="全国"),
        visualmap_opts=opts.VisualMapOpts()  # 分段 is_piecewise=True
    )
    # .render("map_guangdong.html")
)
# st.components.v1.html(c2.render_embed(), height=600)
with st.container(border=True):
    # st.subheader("呼入归属地")
    st.markdown(f'<strong><span style="font-size: 22px; color: blue;">呼入归属地</span></strong>', unsafe_allow_html=True)
    # 使用 st.markdown 和内联 CSS 来创建类似信息框的样式
    info_style = "<style>div.info { color: blue; border: 1px solid #b8daff; padding: 10px; margin: 10px 0; background-color: #e7f2fa; font-size: 20px;}</style>"
    info_text = f"<div class='info'>【当前选择时间范围】：{min_t} 至 {max_t}</div>"
    st.markdown(info_style + info_text, unsafe_allow_html=True)
    col20, col21 = st.columns([1, 1])
    with col20:
        st.components.v1.html(c1.render_embed(), height=600)
    with col21:
        st.components.v1.html(c2.render_embed(), height=600)

# 咨询后第几轮转人工统计
# 提取 aa 列并过滤包含‘转人工服务’的行
filtered_data = QRV_df4[QRV_df4['aa'].str.contains('转人工服务', na=False)]

# 统计包含分号的数量
counts = {
    '第1轮': 0,
    '第2轮': 0,
    '第3轮': 0,
    '第4轮': 0,
    '第5轮': 0,
}

for entry in filtered_data['aa']:
    semicolon_count = entry.count('；')

    if semicolon_count == 1:
        counts['第1轮'] += 1
    elif semicolon_count == 2:
        counts['第2轮'] += 1
    elif semicolon_count == 3:
        counts['第3轮'] += 1
    elif semicolon_count == 4:
        counts['第4轮'] += 1
    elif semicolon_count >= 5:
        counts['第5轮'] += 1

    # 准备绘图数据
x_data = list(counts.keys())
y_data = list(counts.values())


line = (
    Line(init_opts=opts.InitOpts(theme=ThemeType.WONDERLAND, width=f'{WIDTH * 0.5}px',
                                 height=f'{HEIGHT * 0.5}px'))
    .add_xaxis(x_data)
    .add_yaxis('', y_data, label_opts=opts.LabelOpts(is_show=True))
    .set_global_opts(
        tooltip_opts=opts.TooltipOpts(
            trigger='axis',
            axis_pointer_type='cross',
        ),
        title_opts=opts.TitleOpts(title='咨询后第几轮转人工统计'),
        xaxis_opts=opts.AxisOpts(name="对话轮数"),
        yaxis_opts=opts.AxisOpts(name="数量"),
        legend_opts=opts.LegendOpts()
    )
)

# 用户粘性表
# 统计每个call_number的总数
count_series = QRV_df4['call_number'].value_counts()
# 只保留大于1的记录
filtered_count = count_series[count_series > 1]
# 只保留大于2的记录
filtered_count2 = count_series[count_series > 2]

def format_number(num):
    num_str = str(num)
    return num_str[:3] + '*' * 4 + num_str[7:]

# 应用格式化函数
formatted_numbers = filtered_count.index.to_series().apply(format_number)

# 创建新的DataFrame
result_df = pd.DataFrame({
    'call_number2': formatted_numbers,
    'count': filtered_count.values
})
result_df2 = pd.DataFrame({
    'call_number2': filtered_count2.index,
    'count': filtered_count2.values
})

# 显示结果
table5=result_df[['call_number2','count']]
# 重命名列
table5 = table5.rename(columns={
    'call_number2': '手机号',
    'count': '拨打次数',
})
table5=table5.style.background_gradient(subset=['拨打次数'],cmap='Greens')

# 查看详情，20240826新增
call_numbers = result_df2['call_number2'].tolist()
matched_rows = QRV_df4[QRV_df4['call_number'].isin(call_numbers)]
matched_rows['标签'] = np.where(matched_rows['aa'].str.contains('转人工服务', na=False), '转人工', '全机器')
matched_rows = matched_rows[['call_number', '时间', 'result_id' ,'通话时长', '标签', 'thxq']]
matched_rows['通话时长'] = round(matched_rows['通话时长']/60, 1)
matched_rows_sorted = matched_rows.sort_values(by=['call_number', '时间'], ascending=[True, False])
# 将排序后的 DataFrame 赋值给 table6
table8 = matched_rows_sorted
table8 = table8.rename(columns={
    'result_id': '通话ID',
    'call_number': '手机号',
    'thxq': '通话详情',
})

style2={
'通话时长':'{0}分钟'
}

# 加密手机号
table8['手机号'] = table8['手机号'].astype(str)
table8['手机号'] = (table8['手机号'].str[:3] + '****' + table8['手机号'].str[7:])

table8=table8.style.format(style2).background_gradient(subset=['通话时长'],cmap='Greens')


with st.container(border=True):
    # st.subheader("用户粘性")
    st.markdown(f'<strong><span style="font-size: 22px; color: blue;">用户粘性</span></strong>', unsafe_allow_html=True)
    # 使用 st.markdown 和内联 CSS 来创建类似信息框的样式
    info_style = "<style>div.info { color: blue; border: 1px solid #b8daff; padding: 10px; margin: 10px 0; background-color: #e7f2fa; font-size: 20px;}</style>"
    info_text = f"<div class='info'>【当前选择时间范围】：{min_t} 至 {max_t}</div>"
    st.markdown(info_style + info_text, unsafe_allow_html=True)
    col22, col23 = st.columns([2, 1])
    with col22:
        # st.components.v1.html(line_chart.render_embed(),width=WIDTH*0.7, height=HEIGHT*0.7)
        st.components.v1.html(line.render_embed(), width=WIDTH * 0.5, height=HEIGHT * 0.5)
    with col23:
        html_content7 = f'<strong><span style="font-size: 20px;">用户重复呼入次数</span></strong>'
        st.write(html_content7, unsafe_allow_html=True)
        st.dataframe(table5, width=int(WIDTH * 0.15), hide_index=True)
        with st.expander("查看详情 - 3次及以上重呼对话"):
            st.dataframe(table8, hide_index=True)

# 通话时长TOP10
top_tags3 = QRV_df4.nlargest(10, "通话时长").copy()
top_tags3['通话时长'] = round(top_tags3['通话时长']/60, 1)
table6=top_tags3[['通话时长', '时间', 'result_id', 'call_number', 'thxq']]
table6 = table6.rename(columns={
    'result_id': '通话ID',
    'call_number': '手机号',
    'thxq': '通话详情',
})

style={
'通话时长':'{0}分钟'
}

# 加密手机号
table6['手机号'] = table6['手机号'].astype(str)
table6['手机号'] = (table6['手机号'].str[:3] + '****' + table6['手机号'].str[8:])
# print(table6)
table6=table6.style.format(style).background_gradient(subset=['通话时长'],cmap='Greens')


# 周几分时统计
top_3d = QRV_df4.copy()
# 处理数据
top_3d['时间'] = pd.to_datetime(top_3d['时间'])  # 转换为 datetime 对象
top_3d['小时'] = top_3d['时间'].dt.hour      # 提取小时
top_3d['星期'] = top_3d['时间'].dt.dayofweek  # 提取星期，0=Monday, 6=Sunday

# 创建数据列表
data3d = []
for _, row in top_3d.iterrows():
    day_index = row['星期']
    hour_index = row['小时']
    data3d.append([day_index, hour_index, 1])  # 每条记录计为 1 次活动

# 将数据格式化为 [hour_index, day_index, count]
data3d = [[hour, day, sum(1 for d in data3d if d[0] == day and d[1] == hour)] for day in range(7) for hour in range(24)]

# 创建 3D 柱状图
c3 = (
    Bar3D(init_opts=opts.InitOpts(width=f'{WIDTH * 0.5}px', height=f'{HEIGHT * 0.5}px'))
    .add(
        series_name="",
        data=data3d,
        xaxis3d_opts=opts.Axis3DOpts(type_="category", data=[f"{hour}时" for hour in range(24)]),
        yaxis3d_opts=opts.Axis3DOpts(type_="category", data=["周一", "周二", "周三", "周四", "周五", "周六", "周日"]),
        zaxis3d_opts=opts.Axis3DOpts(type_="value"),
    )
    .set_global_opts(
        visualmap_opts=opts.VisualMapOpts(
            max_=30,  # 根据实际数据调整最大值
            range_color=[
                "#313695", "#4575b4", "#74add1", "#abd9e9",
                "#e0f3f8", "#ffffbf", "#fee090", "#fdae61",
                "#f46d43", "#d73027", "#a50026",
            ],
        )
    )
)


with st.container(border=True):
    st.markdown(f'<strong><span style="font-size: 22px; color: blue;">通话时长</span></strong>', unsafe_allow_html=True)
    # 使用 st.markdown 和内联 CSS 来创建类似信息框的样式
    info_style = "<style>div.info { color: blue; border: 1px solid #b8daff; padding: 10px; margin: 10px 0; background-color: #e7f2fa; font-size: 20px;}</style>"
    info_text = f"<div class='info'>【当前选择时间范围】：{min_t} 至 {max_t}</div>"
    st.markdown(info_style + info_text, unsafe_allow_html=True)
    col24, col25 = st.columns([1, 1])
    with col24:
        html_content8 = f'<strong><span style="font-size: 20px;">通话时长TOP10</span></strong>'
        st.write(html_content8, unsafe_allow_html=True)
        st.dataframe(table6, width=int(WIDTH * 0.5), height=int(HEIGHT * 0.4), hide_index=True)
    with col25:
        html_content8 = f'<strong><span style="font-size: 20px;">周中多时段分布</span></strong>'
        st.write(html_content8, unsafe_allow_html=True)
        st.components.v1.html(c3.render_embed(), width=WIDTH * 0.5, height=HEIGHT * 0.5)