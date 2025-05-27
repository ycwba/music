import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from recommender import get_similar_songs
from style_classifier import classify_style, load_style_dict
from lyrics_analyzer import clean_lyrics
import requests

st.set_page_config(
    page_title="智能推荐", 
    page_icon="🎵",
    layout="wide"
)

# 设置中文页面标题和侧边栏
st.markdown("""
<style>
    /* 主标题 */
    .stApp header h1 {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    
    /* 侧边栏标题 */
    [data-testid="stSidebarNav"] {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    
    /* 侧边栏导航项 */
    [data-testid="stSidebarNav"] li div p {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    
    /* 页面内容 */
    .stApp {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    
    /* 导航项图标 */
    [data-testid="stSidebarNav"] ul li:nth-child(1) div p::before {
        content: "🎵 ";
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(2) div p::before {
        content: "📊 ";
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(3) div p::before {
        content: "🎵 ";
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(4) div p::before {
        content: "💾 ";
    }
    
    /* 修复侧边栏标题显示 */
    .css-1d391kg {
        font-family: 'Microsoft YaHei', sans-serif !important;
    }
    
    /* 修复侧边栏导航项显示 */
    .css-1d391kg p {
        font-family: 'Microsoft YaHei', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)
st.title("🎵 智能推荐")

# 初始化session state
if 'song_db' not in st.session_state:
    st.session_state['song_db'] = []
if 'recommendation_history' not in st.session_state:
    st.session_state['recommendation_history'] = []
if 'cache_styles' not in st.session_state:
    st.session_state['cache_styles'] = {}

def get_song_style(song):
    """获取歌曲风格"""
    if song['id'] not in st.session_state['cache_styles']:
        cleaned_lyric = clean_lyrics(song['lyric'], song['artist'])
        st.session_state['cache_styles'][song['id']] = classify_style(cleaned_lyric, load_style_dict())[0]
    return st.session_state['cache_styles'][song['id']]

def add_to_history(base_song, recommended_songs, mode="song_based", filters=None):
    """添加推荐记录到历史"""
    history_entry = {
        'timestamp': datetime.now(),
        'mode': mode,
        'recommended_songs': recommended_songs
    }
    
    if mode == "song_based":
        history_entry['base_song'] = base_song
    else:  # multi_filter
        history_entry['filters'] = filters
    
    st.session_state['recommendation_history'].append(history_entry)
    # 只保留最近20条记录
    if len(st.session_state['recommendation_history']) > 20:
        st.session_state['recommendation_history'] = st.session_state['recommendation_history'][-20:]

# 检查是否有数据
if not st.session_state['song_db']:
    st.info("暂无歌词数据。请在'数据导入导出'页面添加歌词。")
else:
    # 创建两列布局
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("推荐设置")

        # 获取所有歌手和风格列表
        all_artists = list(set(song['artist'] for song in st.session_state['song_db']))
        all_styles = list(set(st.session_state['cache_styles'].values())) if st.session_state['cache_styles'] else []
        
        # 推荐方式选择
        recommendation_mode = st.radio(
            "推荐方式",
            ["基于歌曲", "多重筛选"],
            horizontal=True
        )

        if recommendation_mode == "基于歌曲":
            # 选择基准歌曲
            song_options = [f"{song['title']} - {song['artist']}" for song in st.session_state['song_db']]
            selected_song = st.selectbox("选择歌曲", song_options)
            
            if selected_song:
                song_idx = song_options.index(selected_song)
                base_song = st.session_state['song_db'][song_idx]
                
                # 显示基准歌曲信息
                st.write("基准歌曲信息：")
                st.write(f"- 歌手：{base_song['artist']}")
                st.write(f"- 风格：{get_song_style(base_song)}")
                
                # 推荐参数设置
                num_recommendations = st.slider("推荐数量", 1, 10, 5)
                consider_style = st.checkbox("考虑歌曲风格", value=True)
                
                if st.button("获取推荐"):
                    # 获取推荐结果
                    recommended = get_similar_songs(
                        base_song,
                        st.session_state['song_db'],
                        n_recommendations=num_recommendations,
                        consider_style=consider_style
                    )
                    
                    # 添加到历史记录
                    add_to_history(base_song, recommended, mode="song_based")
                    
                    # 显示推荐结果
                    st.write("### 推荐结果")
                    for i, rec in enumerate(recommended, 1):
                        encoded_title = requests.utils.quote(rec['title'])
                        st.write(f"{i}. **[{rec['title']}](https://www.last.fm/search?q={encoded_title})** - {rec['artist']}")
                        st.write(f"   风格：{get_song_style(rec)}")
                        with st.expander("查看歌词"):
                            st.text(rec['lyric'])

        else:  # 多重筛选模式
            col1_inner, col2_inner = st.columns(2)
            
            with col1_inner:
                # 歌手多选
                selected_artists = st.multiselect(
                    "选择歌手(可多选)", 
                    all_artists,
                    default=None
                )
            
            with col2_inner:
                # 风格多选
                selected_styles = st.multiselect(
                    "选择风格(可多选)",
                    all_styles,
                    default=None
                )
            
            # 推荐参数
            num_recommendations = st.slider("推荐数量", 1, 10, 5)
            
            if st.button("获取推荐"):
                # 筛选歌曲
                filtered_songs = st.session_state['song_db']
                
                # 应用歌手筛选
                if selected_artists:
                    filtered_songs = [
                        song for song in filtered_songs
                        if song['artist'] in selected_artists
                    ]
                
                # 应用风格筛选
                if selected_styles:
                    filtered_songs = [
                        song for song in filtered_songs
                        if get_song_style(song) in selected_styles
                    ]
                    
                # 检查筛选结果
                if not filtered_songs:
                    st.warning("没有找到符合条件的歌曲，请调整筛选条件")
                else:
                    # 显示筛选统计
                    st.write(f"### 找到 {len(filtered_songs)} 首符合条件的歌曲")
                    
                    # 如果筛选结果太多，随机选取部分展示
                    display_count = min(10, len(filtered_songs))
                    display_songs = np.random.choice(
                        filtered_songs,
                        size=display_count,
                        replace=False
                    )
                    
                    # 显示部分结果预览
                    with st.expander("预览部分歌曲"):
                        for song in display_songs:
                            st.write(f"- **{song['title']}** - {song['artist']} ({get_song_style(song)})")
                    
                    # 如果用户要求的推荐数量比实际歌曲少，调整数量
                    actual_recommendations = min(num_recommendations, len(filtered_songs))
                    
                    # 随机推荐
                    recommended = np.random.choice(
                        filtered_songs,
                        size=actual_recommendations,
                        replace=False
                    ).tolist()
                    
                    # 准备筛选条件信息用于历史记录
                    filters = {
                        'artists': selected_artists if selected_artists else [],
                        'styles': selected_styles if selected_styles else []
                    }
                    
                    # 添加到历史记录
                    add_to_history(None, recommended, mode="multi_filter", filters=filters)
                    
                    # 显示推荐结果
                    st.write(f"### 为您推荐 {actual_recommendations} 首歌曲")
                    for i, rec in enumerate(recommended, 1):
                        encoded_title = requests.utils.quote(rec['title'])
                        st.write(f"{i}. **[{rec['title']}](https://www.last.fm/search?q={encoded_title})** - {rec['artist']}")
                        st.write(f"   风格：{get_song_style(rec)}")
                        with st.expander("查看歌词"):
                            st.text(rec['lyric'])

    with col2:
        st.subheader("推荐历史")
        
        if st.session_state['recommendation_history']:
            for history in reversed(st.session_state['recommendation_history']):
                # 根据推荐模式生成不同的标题
                if history['mode'] == "song_based":
                    title = f"基于《{history['base_song']['title']}》的推荐"
                else:  # multi_filter
                    filter_parts = []
                    if history['filters']['artists']:
                        filter_parts.append(f"歌手: {', '.join(history['filters']['artists'])}")
                    if history['filters']['styles']:
                        filter_parts.append(f"风格: {', '.join(history['filters']['styles'])}")
                    filter_desc = " | ".join(filter_parts) if filter_parts else "全部歌曲"
                    title = f"多重筛选推荐 ({filter_desc})"
                
                with st.expander(
                    f"{title} - {history['timestamp'].strftime('%Y-%m-%d %H:%M')}"
                ):
                    # 显示推荐条件
                    if history['mode'] == "song_based":
                        st.write("**基准歌曲：**")
                        base_song = history['base_song']
                        encoded_title = requests.utils.quote(base_song['title'])
                        st.write(f"- **[{base_song['title']}](https://www.last.fm/search?q={encoded_title})** - "
                                f"{base_song['artist']}")
                    else:
                        st.write("**筛选条件：**")
                        if history['filters']['artists']:
                            st.write(f"- 歌手: {', '.join(history['filters']['artists'])}")
                        if history['filters']['styles']:
                            st.write(f"- 风格: {', '.join(history['filters']['styles'])}")
                        if not history['filters']['artists'] and not history['filters']['styles']:
                            st.write("- 无特定筛选条件（全部歌曲）")
                    
                    st.write("**推荐歌曲：**")
                    for i, rec in enumerate(history['recommended_songs'], 1):
                        encoded_title = requests.utils.quote(rec['title'])
                        st.write(f"{i}. **[{rec['title']}](https://www.last.fm/search?q={encoded_title})** - {rec['artist']}")
        else:
            st.info("暂无推荐历史记录")