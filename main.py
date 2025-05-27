import streamlit as st
import time

# 初始化session state
if 'song_db' not in st.session_state:
    st.session_state['song_db'] = []
if 'delete_flags' not in st.session_state:
    st.session_state['delete_flags'] = {}
if 'highlight_imports' not in st.session_state:
    st.session_state['highlight_imports'] = {}
if 'editing_song' not in st.session_state:
    st.session_state['editing_song'] = None
if 'last_import_time' not in st.session_state:
    st.session_state['last_import_time'] = 0
if 'need_refresh' not in st.session_state:
    st.session_state['need_refresh'] = False
if 'cache_keywords' not in st.session_state:
    st.session_state['cache_keywords'] = {}
if 'cache_styles' not in st.session_state:
    st.session_state['cache_styles'] = {}
if 'recommendation_history' not in st.session_state:
    st.session_state['recommendation_history'] = []
if 'import_history' not in st.session_state:
    st.session_state['import_history'] = []
if 'cache_analysis' not in st.session_state:
    st.session_state['cache_analysis'] = {}

st.set_page_config(
    page_title="歌词NLP分析与推荐系统",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
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
</style>
""", unsafe_allow_html=True)

# 页面样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        color: #4B5563;
    }
    .feature-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 10px;
        color: #6366F1;
    }
    .feature-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .feature-description {
        color: #4B5563;
    }
    .stats-container {
        background-color: #EEF2FF;
        border-radius: 10px;
        padding: 20px;
        margin-top: 30px;
    }
    .stat-item {
        text-align: center;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #4F46E5;
    }
    .stat-label {
        color: #4B5563;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        padding: 20px;
        color: #6B7280;
        border-top: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# 主页面标题
st.markdown('<h1 class="main-header">🎵 歌词NLP分析与推荐系统</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">智能分析歌词内容，发现创作风格，推荐相似歌曲</p>', unsafe_allow_html=True)

# 系统概述
st.markdown("## 系统概述")
st.write("""
这个系统使用自然语言处理技术分析歌词内容，帮助你理解歌词的主题、情感和风格特点。
你可以上传歌词文件、输入歌词文本，系统会自动分析并提供词频统计、关键词提取、风格分类等功能。
此外，系统还能根据你的喜好智能推荐相似风格的歌曲。
""")

# 功能模块展示
st.markdown("## 主要功能")

# 使用container和label来避免空标签警告
with st.container():
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 左侧功能", help="左侧功能区域")  # 添加标签
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📝</div>
            <div class="feature-title">歌词管理</div>
            <div class="feature-description">
                <ul>
                    <li>统一的歌词列表视图</li>
                    <li>支持批量操作（删除、编辑）</li>
                    <li>歌词分类和标签功能</li>
                    <li>搜索和过滤功能</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎵</div>
            <div class="feature-title">智能推荐</div>
            <div class="feature-description">
                <ul>
                    <li>基于歌曲内容的智能推荐</li>
                    <li>基于风格的歌曲推荐</li>
                    <li>基于歌手的相似推荐</li>
                    <li>推荐历史记录</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 右侧功能", help="右侧功能区域")  # 添加标签
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">歌词分析</div>
            <div class="feature-description">
                <ul>
                    <li>词频统计与可视化</li>
                    <li>词云生成</li>
                    <li>TF-IDF关键词提取</li>
                    <li>风格分布分析</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💾</div>
            <div class="feature-title">数据导入导出</div>
            <div class="feature-description">
                <ul>
                    <li>多种导入方式（文件、文本）</li>
                    <li>批量导入功能</li>
                    <li>数据导出为JSON/TXT</li>
                    <li>数据备份与恢复</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 系统统计信息
st.markdown("## 系统统计")

with st.container():
    stats_col1, stats_col2, stats_col3 = st.columns(3)

    with stats_col1:
        st.markdown("### 歌曲统计", help="显示系统中的歌曲总数")  # 添加标签
        st.markdown("""
        <div class="stat-item">
            <div class="stat-value">{}</div>
            <div class="stat-label">歌曲总数</div>
        </div>
        """.format(len(st.session_state['song_db'])), unsafe_allow_html=True)

    with stats_col2:
        st.markdown("### 歌手统计", help="显示系统中的歌手数量")  # 添加标签
        artists_count = len(set(song['artist'] for song in st.session_state['song_db'])) if st.session_state['song_db'] else 0
        st.markdown("""
        <div class="stat-item">
            <div class="stat-value">{}</div>
            <div class="stat-label">歌手数量</div>
        </div>
        """.format(artists_count), unsafe_allow_html=True)

    with stats_col3:
        st.markdown("### 风格统计", help="显示系统中的风格类型数量")  # 添加标签
        styles_count = len(set(st.session_state['cache_styles'].values())) if st.session_state['cache_styles'] else 0
        st.markdown("""
        <div class="stat-item">
            <div class="stat-value">{}</div>
            <div class="stat-label">风格类型</div>
        </div>
        """.format(styles_count), unsafe_allow_html=True)

# 快速入门指南
st.markdown("## 快速入门")
st.write("""
1. **数据导入**：在"数据导入导出"页面添加歌词数据
2. **歌词管理**：在"歌词管理"页面查看和编辑歌词
3. **歌词分析**：在"歌词分析"页面查看词频统计、词云和关键词
4. **智能推荐**：在"智能推荐"页面获取相似歌曲推荐
""")

# 页面导航
st.markdown("## 功能导航")
with st.container():
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

    with nav_col1:
        st.markdown("### 管理功能", help="跳转到歌词管理页面")  # 添加标签
        if st.button("📝 管理歌词库", use_container_width=True):
            st.switch_page("pages/1_lyrics_management.py")

    with nav_col2:
        st.markdown("### 分析功能", help="跳转到分析统计页面")  # 添加标签
        if st.button("📊 分析与统计", use_container_width=True):
            st.switch_page("pages/2_lyrics_analysis.py")

    with nav_col3:
        st.markdown("### 推荐功能", help="跳转到智能推荐页面")  # 添加标签
        if st.button("🎵 相似推荐", use_container_width=True):
            st.switch_page("pages/3_smart_recommendation.py")

    with nav_col4:
        st.markdown("### 数据功能", help="跳转到数据导入导出页面")  # 添加标签
        if st.button("💾 导入与导出", use_container_width=True):
            st.switch_page("pages/4_data_import_export.py")

# 页脚
st.markdown("""
<div class="footer">
    <p>歌词NLP分析与推荐系统 © 2023</p>
</div>
""", unsafe_allow_html=True)