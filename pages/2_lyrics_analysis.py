import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba.analyse
from lyrics_analyzer import clean_lyrics
from style_classifier import classify_style, load_style_dict
import matplotlib as mpl
import platform
import os

st.set_page_config(
    page_title="歌词分析", 
    page_icon="📊",
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
        content: "� ";
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
</style>
""", unsafe_allow_html=True)

# 设置matplotlib中文字体
def set_matplotlib_chinese_font():
    if platform.system() == "Windows":
        # Windows系统使用微软雅黑
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    elif platform.system() == "Darwin":
        # macOS系统使用苹方字体
        plt.rcParams['font.sans-serif'] = ['PingFang HK']
    else:
        # Linux系统使用文泉驿微米黑
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
    
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 初始化matplotlib中文字体
set_matplotlib_chinese_font()
st.title("📊 歌词分析")

# 初始化session state
if 'song_db' not in st.session_state:
    st.session_state['song_db'] = []
if 'cache_analysis' not in st.session_state:
    st.session_state['cache_analysis'] = {}

def get_all_lyrics():
    """获取所有歌词文本"""
    return [song['lyric'] for song in st.session_state['song_db']]

def get_all_artists():
    """获取所有歌手"""
    return list(set(song['artist'] for song in st.session_state['song_db']))

def create_word_cloud(text):
    """生成词云图"""
    # 检查输入文本
    if not text or len(text.strip()) < 2:
        raise ValueError("输入文本过短，无法生成词云")

    # 使用jieba分词
    words = jieba.lcut(text)
    # 过滤掉单字词和停用词
    words = [word for word in words if len(word) > 1]
    
    if not words:
        raise ValueError("分词结果为空，无法生成词云")
    
    # 将词语重新组合
    text = " ".join(words)
    
    # 根据不同操作系统选择合适的字体
    if platform.system() == "Windows":
        font_paths = [
            'C:/Windows/Fonts/simhei.ttf',  # 黑体
            'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
            'C:/Windows/Fonts/simsun.ttc'   # 宋体
        ]
    elif platform.system() == "Darwin":
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc'
        ]
    else:
        font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
        ]
    
    # 尝试不同的字体
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    try:
        wordcloud = WordCloud(
            font_path=font_path if font_path else None,
            width=800,
            height=400,
            background_color='white',
            max_words=200,
            max_font_size=150,
            random_state=42,
            min_word_length=2,  # 最小词长度
            collocations=False  # 避免重复词语
        )
        
        # 生成词云
        wordcloud.generate(text)
        return wordcloud
        
    except FileNotFoundError:
        st.warning("未找到合适的中文字体，尝试使用系统默认字体")
        # 使用默认字体
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=200,
            max_font_size=150,
            random_state=42,
            min_word_length=2,
            collocations=False
        )
        wordcloud.generate(text)
        return wordcloud
    except Exception as e:
        raise Exception(f"生成词云时出错: {str(e)}")

# 检查是否有数据
if not st.session_state['song_db']:
    st.info("暂无歌词数据。请在'数据导入导出'页面添加歌词。")
else:
    # 创建分析面板
    tab1, tab2, tab3, tab4 = st.tabs([
        "词频统计 📈", 
        "词云展示 ☁️", 
        "关键词分析 🔍",
        "风格分布 🎨"
    ])

    with tab1:
        st.subheader("词频统计分析")
        
        # 选择分析范围
        analysis_scope = st.radio(
            "分析范围",
            ["所有歌词", "按歌手筛选"],
            horizontal=True
        )

        if analysis_scope == "按歌手筛选":
            selected_artist = st.selectbox("选择歌手", get_all_artists())
            lyrics_to_analyze = [
                song['lyric'] for song in st.session_state['song_db']
                if song['artist'] == selected_artist
            ]
        else:
            lyrics_to_analyze = get_all_lyrics()

        # 词频分析
        if lyrics_to_analyze:
            # 合并所有歌词并清洗
            combined_lyrics = " ".join(lyrics_to_analyze)
            cleaned_lyrics = clean_lyrics(combined_lyrics)
            
            # 统计词频
            if cleaned_lyrics and cleaned_lyrics != "示例歌词":
                words = jieba.lcut(cleaned_lyrics)
                word_freq = Counter()
                
                # 过滤掉单字词和停用词，并添加到Counter中
                for word, freq in Counter(words).items():
                    if len(word) > 1:
                        word_freq[word] = freq
                
                if word_freq:
                    # 展示词频统计
                    df = pd.DataFrame(
                        word_freq.most_common(20),
                        columns=['词语', '出现次数']
                    )
                    
                    col1, col2 = st.columns([2, 3])
                    
                    with col1:
                        st.write("### 词频统计表")
                        st.dataframe(df, use_container_width=True)
                    
                    with col2:
                        st.write("### 词频分布图")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        bars = ax.bar(df['词语'], df['出现次数'])
                        
                        # 在柱状图上添加数值标签
                        for bar in bars:
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                  f'{int(height)}',
                                  ha='center', va='bottom')
                        
                        plt.xticks(rotation=45, ha='right')
                        plt.title("词频分布")
                        # 调整布局，确保文字标签不被截断
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close()
                else:
                    st.warning("未找到有效的词语进行统计")
            else:
                st.warning("请先输入或选择要分析的歌词")

    with tab2:
        st.subheader("词云可视化")
        
        # 词云生成选项
        cloud_scope = st.radio(
            "词云范围",
            ["所有歌词", "按歌手生成"],
            horizontal=True
        )

        if cloud_scope == "按歌手生成":
            selected_artist = st.selectbox(
                "选择歌手",
                get_all_artists(),
                key="cloud_artist"
            )
            lyrics_for_cloud = " ".join([
                song['lyric'] for song in st.session_state['song_db']
                if song['artist'] == selected_artist
            ])
        else:
            lyrics_for_cloud = " ".join(get_all_lyrics())

        if lyrics_for_cloud:
            with st.spinner("正在生成词云..."):
                try:
                    # 清洗歌词文本
                    cleaned_lyrics = clean_lyrics(lyrics_for_cloud)
                    
                    # 检查清洗后的文本是否为空
                    if not cleaned_lyrics or cleaned_lyrics == "示例歌词":
                        st.warning("清洗后的歌词文本为空，无法生成词云。请尝试其他歌词。")
                    else:
                        try:
                            # 生成词云
                            wordcloud = create_word_cloud(cleaned_lyrics)
                            
                            # 显示词云图
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                            plt.close()
                            
                            # 显示词频统计
                            words = jieba.lcut(cleaned_lyrics)
                            word_counts = Counter([w for w in words if len(w) > 1])
                            if word_counts:
                                st.write("### 词频统计")
                                word_df = pd.DataFrame(word_counts.most_common(15), columns=['词语', '出现次数'])
                                st.dataframe(word_df, use_container_width=True)
                            
                        except ValueError as ve:
                            st.warning(f"无法生成词云: {str(ve)}")
                            st.info("提示: 请尝试包含更多有意义的词语的歌词。")
                        except Exception as e:
                            st.error(f"生成词云时出错: {str(e)}")
                            st.info("请尝试其他歌词或检查歌词内容。")
                except Exception as e:
                    st.error(f"处理歌词时出错: {str(e)}")

    with tab3:
        st.subheader("TF-IDF关键词分析")
        
        # 选择分析对象
        analysis_target = st.radio(
            "分析对象",
            ["单首歌词", "歌手创作"],
            horizontal=True
        )

        if analysis_target == "单首歌词":
            # 选择具体歌曲
            song_options = [f"{song['title']} - {song['artist']}" for song in st.session_state['song_db']]
            selected_song = st.selectbox("选择歌曲", song_options)
            
            if selected_song:
                song_idx = song_options.index(selected_song)
                song = st.session_state['song_db'][song_idx]
                
                # 提取关键词
                keywords = jieba.analyse.extract_tags(
                    song['lyric'],
                    topK=10,
                    withWeight=True
                )
                
                # 显示关键词
                st.write("关键词权重分布：")
                fig, ax = plt.subplots(figsize=(10, 5))
                keywords_df = pd.DataFrame(keywords, columns=['关键词', '权重'])
                ax.barh(keywords_df['关键词'], keywords_df['权重'])
                plt.title("关键词 TF-IDF 权重")
                st.pyplot(fig)
                plt.close()

        else:  # 歌手创作分析
            selected_artist = st.selectbox(
                "选择歌手",
                get_all_artists(),
                key="tfidf_artist"
            )
            
            if selected_artist:
                # 获取该歌手的所有歌词
                artist_lyrics = " ".join([
                    song['lyric'] for song in st.session_state['song_db']
                    if song['artist'] == selected_artist
                ])
                
                # 提取关键词
                keywords = jieba.analyse.extract_tags(
                    artist_lyrics,
                    topK=15,
                    withWeight=True
                )
                
                # 显示关键词
                st.write(f"{selected_artist} 创作关键词：")
                keywords_df = pd.DataFrame(keywords, columns=['关键词', '权重'])
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(keywords_df, use_container_width=True)
                
                with col2:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.bar(keywords_df['关键词'], keywords_df['权重'])
                    plt.xticks(rotation=45, ha='right')
                    plt.title("创作关键词权重分布")
                    st.pyplot(fig)
                    plt.close()

    with tab4:
        st.subheader("歌词风格分布分析")
        
        # 计算所有歌词的风格
        style_dict = load_style_dict()
        
        # 统计风格分布
        style_stats = Counter()
        for song in st.session_state['song_db']:
            cleaned_lyric = clean_lyrics(song['lyric'], song['artist'])
            style = classify_style(cleaned_lyric, style_dict)[0]
            style_stats[style] += 1
        
        # 创建风格分布图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 条形图
        styles = list(style_stats.keys())
        counts = list(style_stats.values())
        ax1.bar(styles, counts)
        ax1.set_title("风格分布")
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 饼图
        ax2.pie(counts, labels=styles, autopct='%1.1f%%')
        ax2.set_title("风格占比")
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        
        # 按歌手显示风格分布
        st.subheader("歌手风格倾向")
        
        selected_artist = st.selectbox(
            "选择歌手",
            get_all_artists(),
            key="style_artist"
        )
        
        if selected_artist:
            # 统计该歌手的风格分布
            artist_style_stats = Counter()
            artist_songs = [
                song for song in st.session_state['song_db']
                if song['artist'] == selected_artist
            ]
            
            for song in artist_songs:
                cleaned_lyric = clean_lyrics(song['lyric'], song['artist'])
                style = classify_style(cleaned_lyric, style_dict)[0]
                artist_style_stats[style] += 1
            
            # 创建该歌手的风格分布图表
            fig, ax = plt.subplots(figsize=(10, 6))
            styles = list(artist_style_stats.keys())
            counts = list(artist_style_stats.values())
            
            ax.bar(styles, counts)
            ax.set_title(f"{selected_artist} 的创作风格分布")
            plt.xticks(rotation=45, ha='right')
            
            st.pyplot(fig)
            plt.close()