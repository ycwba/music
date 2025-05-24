import streamlit as st
import time
from lyrics_analyzer import clean_lyrics
from style_classifier import load_style_dict, classify_style

st.set_page_config(
    page_title="歌词管理", 
    page_icon="📝",
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

st.title("📝 歌词管理")

# 初始化session state（如果需要）
if 'song_db' not in st.session_state:
    st.session_state['song_db'] = []
if 'delete_flags' not in st.session_state:
    st.session_state['delete_flags'] = {}
if 'highlight_imports' not in st.session_state:
    st.session_state['highlight_imports'] = {}
if 'editing_song' not in st.session_state:
    st.session_state['editing_song'] = None
if 'cache_styles' not in st.session_state:
    st.session_state['cache_styles'] = {}

def mark_delete(song_id, flag):
    st.session_state['delete_flags'][song_id] = flag

def save_deletions():
    st.session_state['song_db'] = [s for s in st.session_state['song_db'] if not st.session_state['delete_flags'].get(s['id'], False)]
    st.session_state['delete_flags'] = {}
    st.rerun()

def delete_song(song_id):
    st.session_state['song_db'] = [s for s in st.session_state['song_db'] if s['id'] != song_id]
    st.session_state['cache_styles'].pop(song_id, None)
    st.rerun()

def edit_song(song_id):
    st.session_state['editing_song'] = song_id

def save_edit(song_id, new_artist, new_title, new_lyric):
    for song in st.session_state['song_db']:
        if song['id'] == song_id:
            song['artist'] = new_artist
            song['title'] = new_title
            song['lyric'] = new_lyric
            break
    st.session_state['editing_song'] = None
    st.session_state['cache_styles'].pop(song_id, None)

# 样式设置
st.markdown("""
<style>
    .song-container {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .song-container:hover {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# 歌词列表视图
if st.session_state['song_db']:
    # 搜索和过滤功能
    col1, col2 = st.columns([2, 2])
    with col1:
        search_term = st.text_input("搜索歌词", placeholder="输入歌手名、歌名或歌词内容")
    with col2:
        style_filter = st.selectbox(
            "按风格筛选",
            ["全部"] + list(set(st.session_state['cache_styles'].values())),
            index=0
        )
    
    # 批量操作按钮
    if st.button("删除所选"):
        save_deletions()

    # 显示歌词列表
    for song in st.session_state['song_db']:
        # 搜索过滤
        if search_term and not any(search_term.lower() in x.lower() for x in [song['artist'], song['title'], song['lyric']]):
            continue
            
        # 风格过滤
        if song['id'] not in st.session_state['cache_styles']:
            cleaned_lyric = clean_lyrics(song['lyric'], song['artist'])
            st.session_state['cache_styles'][song['id']] = classify_style(cleaned_lyric, load_style_dict())[0]
        if style_filter != "全部" and st.session_state['cache_styles'][song['id']] != style_filter:
            continue

        with st.container():
            st.markdown("---")
            cols = st.columns([0.5, 0.5, 0.5, 3.5])
            
            with cols[0]:
                if st.button("✏️", key=f"edit_{song['id']}"):
                    edit_song(song['id'])
                    st.rerun()
            
            with cols[1]:
                if st.button("🗑️", key=f"delete_{song['id']}"):
                    delete_song(song['id'])
            
            with cols[2]:
                delete_flag = st.checkbox("", key=f"select_{song['id']}", 
                                       value=st.session_state['delete_flags'].get(song['id'], False))
                mark_delete(song['id'], delete_flag)
            
            with cols[3]:
                if st.session_state['editing_song'] == song['id']:
                    # 编辑表单
                    new_artist = st.text_input("歌手名", value=song['artist'], key=f"edit_artist_{song['id']}")
                    new_title = st.text_input("歌曲名", value=song['title'], key=f"edit_title_{song['id']}")
                    new_lyric = st.text_area("歌词内容", value=song['lyric'], height=200, key=f"edit_lyric_{song['id']}")
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("保存", key=f"save_{song['id']}"):
                            save_edit(song['id'], new_artist, new_title, new_lyric)
                            st.rerun()
                    with col2:
                        if st.button("取消", key=f"cancel_{song['id']}"):
                            st.session_state['editing_song'] = None
                            st.rerun()
                else:
                    # 显示歌词信息
                    st.markdown(
                        f"<div>"
                        f"**{song['title']}** | {song['artist']} | "
                        f"<span style='color:gray'>风格：{st.session_state['cache_styles'][song['id']]}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    if st.button("查看歌词", key=f"view_{song['id']}"):
                        st.code(song['lyric'], language='text')
else:
    st.info("暂无歌词数据。请在'数据导入导出'页面添加歌词。")