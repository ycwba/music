import streamlit as st
import json
import pandas as pd
from datetime import datetime
import uuid
import time
import numpy as np
import re
import os
from lyrics_analyzer import clean_lyrics
from style_classifier import classify_style, load_style_dict


st.set_page_config(
    page_title="数据导入导出", 
    page_icon="💾",
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
        content: "📊 ";
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(2) div p::before {
        content: "🔍 ";
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(3) div p::before {
        content: "🎵 ";
    }
    
    [data-testid="stSidebarNav"] ul li:nth-child(4) div p::before {
        content: "💾 ";
    }
</style>
""", unsafe_allow_html=True)
st.title("💾 数据导入导出")

# 初始化session state
if 'song_db' not in st.session_state:
    st.session_state['song_db'] = []
if 'import_history' not in st.session_state:
    st.session_state['import_history'] = []
if 'highlight_imports' not in st.session_state:
    st.session_state['highlight_imports'] = {}


def parse_lrc(content):
    """解析LRC文件内容"""
    artist = "未知歌手"
    title = "未知歌曲"
    lyrics = []
    has_lyrics = False
    
    # 标准LRC标签映射
    standard_tags = {
        'ar': 'artist',
        'ti': 'title',
        'al': 'album',
        'by': 'creator',
        'artist': 'artist',
        'title': 'title',
        'album': 'album',
        'creator': 'creator'
    }
    
    # 用于提取歌手和歌名的信息
    metadata = {
        'artist': None,
        'title': None
    }
    
    # 需要过滤的信息标记
    filter_keywords = [
        "作词", "作曲", "编曲", "制作人", "监制", "混音", "录音",
        "企划", "统筹", "出品", "发行", "歌词", "曲", "词",
        "Lyrics", "Music", "Composer", "Arranger", "Producer",
        "Mixing", "Recording", "Mastering", "Label", "Copyright"
    ]
    
    # 处理每一行
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 如果是带标记的行
        if line.startswith('['):
            # 检查是否是标准LRC标签 [ar:歌手名] 或 [ti:歌曲名]
            if ':' in line and ']' in line:
                tag_part = line[1:line.find(':')].lower()
                if tag_part in standard_tags:
                    value = line[line.find(':')+1:line.find(']')].strip()
                    if standard_tags[tag_part] == 'artist' and value:
                        metadata['artist'] = value
                    elif standard_tags[tag_part] == 'title' and value:
                        metadata['title'] = value
                    continue
            
            # 处理时间标记行 [00:00.00]歌词
            parts = line.split(']')
            if len(parts) > 1:
                # 检查第一部分是否是时间标记 [00:00.00]
                time_part = parts[0][1:]
                if ':' in time_part and all(c.isdigit() or c in ':.,' for c in time_part):
                    content_part = parts[-1].strip()
                    
                    # 检查是否是元数据信息
                    if any(keyword in content_part for keyword in filter_keywords):
                        # 尝试从这些行提取歌手信息
                        if "作词" in content_part or "作曲" in content_part or "Lyrics" in content_part or "Music" in content_part:
                            try:
                                parts = content_part.split(":", 1)
                                if len(parts) > 1:
                                    artist_name = parts[1].strip()
                                    if not metadata['artist'] and len(artist_name) > 1:
                                        metadata['artist'] = artist_name
                            except:
                                pass
                        continue
                    
                    # 如果不是元数据且内容不为空，则认为是歌词
                    if content_part and not any(keyword in content_part for keyword in filter_keywords):
                        lyrics.append(content_part)
                        has_lyrics = True
        
        # 处理特殊标签
        elif line.startswith('@') or line.startswith('【'):
            # 尝试从特殊标签中提取信息
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    tag = parts[0].strip().lower()
                    value = parts[1].strip()
                    if 'artist' in tag or '歌手' in tag:
                        metadata['artist'] = value
                    elif 'title' in tag or '歌名' in tag:
                        metadata['title'] = value
            continue
        
        # 处理无时间标记的普通行
        else:
            # 过滤掉元数据信息
            if not any(keyword in line for keyword in filter_keywords):
                lyrics.append(line)
                has_lyrics = True
    
    # 使用提取到的元数据
    if metadata['artist']:
        artist = metadata['artist']
    if metadata['title']:
        title = metadata['title']
    
    # 如果已经识别到歌手名但还没有识别到歌曲名，尝试从歌词中提取
    if artist != "未知歌手" and title == "未知歌曲":
        for line in lyrics:
            if ' - ' in line:
                parts = line.split(' - ')
                if len(parts) >= 2:
                    potential_title = parts[0].strip()
                    if '(' in potential_title:
                        potential_title = potential_title.split('(')[0].strip()
                    if potential_title and not any(keyword in potential_title for keyword in filter_keywords):
                        title = potential_title
                        break
    
    # 从歌词中移除包含歌曲名的行
    if title != "未知歌曲":
        lyrics = [line for line in lyrics if title not in line]
    
    return {
        'artist': artist,
        'title': title,
        'lyric': '\n'.join(lyrics) if has_lyrics else ""
    }

def export_to_json(songs):
    """导出歌曲数据为JSON格式"""
    return json.dumps(songs, ensure_ascii=False, indent=2)

def validate_song_data(artist, title, lyric):
    """验证歌曲数据"""
    if not artist or not title or not lyric:
        return False, "歌手名、歌曲名和歌词内容不能为空"
    if len(artist) > 100 or len(title) > 100:
        return False, "歌手名和歌曲名长度不能超过100个字符"
    if len(lyric) > 10000:
        return False, "歌词内容不能超过10000个字符"
    return True, ""

def add_song(artist, title, lyric):
    """添加歌曲到数据库"""
    song_id = str(uuid.uuid4())
    song = {
        'id': song_id,
        'artist': artist,
        'title': title,
        'lyric': lyric,
        'import_time': datetime.now().isoformat()
    }
    st.session_state['song_db'].append(song)
    
    # 记录导入历史
    st.session_state['import_history'].append({
        'timestamp': datetime.now(),
        'action': 'import',
        'details': f"{title} - {artist}"
    })


# 创建两列布局
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("数据导入")
    
    # 创建选项卡
    tab1, tab2 = st.tabs([
        "手动输入 ✍️", 
        "文件上传 📁"
    ])
    
    with tab1:
        # 手动输入表单
        with st.form("manual_input_form"):
            artist = st.text_input("歌手名")
            title = st.text_input("歌曲名")
            lyric = st.text_area("歌词内容", height=200)
            
            submitted = st.form_submit_button("添加歌曲")
            if submitted:
                valid, error_msg = validate_song_data(artist, title, lyric)
                if valid:
                    add_song(artist, title, lyric)
                    st.success(f"成功添加歌曲：{title} - {artist}")
                else:
                    st.error(error_msg)
    
    with tab2:
        # 多文件上传功能 - 确保不在表单内
        st.write("支持的文件格式：")
        st.write("- JSON文件（单首或多首歌曲）")
        st.write("- TXT文件（每首歌曲需包含歌手名和歌曲名）")
        st.write("- LRC文件（带时间标记的歌词文件）")
        
        uploaded_files = st.file_uploader(
            "选择文件（可多选）", 
            type=['json', 'txt', 'lrc'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            total_files = len(uploaded_files)
            success_count = 0
            
            # 一键导入按钮 - 确保不在form内
            if st.button("✨ 一键导入所有文件", use_container_width=True, type="primary"):
                with st.spinner(f"正在批量导入 {total_files} 个文件..."):
                    for uploaded_file in uploaded_files:
                        try:
                            content = uploaded_file.getvalue().decode('utf-8')
                            file_type = uploaded_file.name.split('.')[-1].lower()
                            filename = uploaded_file.name
                            default_title = filename[:-4] if filename.lower().endswith('.lrc') else filename
                            default_title = re.sub(r'[\\/*?:"<>|]', "", default_title).strip()
                            
                            if file_type == 'lrc':
                                lrc_data = parse_lrc(content)
                                if 'error' not in lrc_data:
                                    artist = lrc_data.get('artist', "未知歌手")
                                    title = lrc_data.get('title', "未知歌曲")
                                    if title == "未知歌曲":
                                        title = default_title
                                    lyric = lrc_data.get('lyric', "")
                                    valid, _ = validate_song_data(artist, title, lyric)
                                    if valid:
                                        add_song(artist, title, lyric)
                                        success_count += 1
                            
                            elif file_type == 'json':
                                data = json.loads(content)
                                if isinstance(data, list):
                                    for song in data:
                                        if all(k in song for k in ['artist', 'title', 'lyric']):
                                            artist = song.get('artist', "未知歌手")
                                            title = song.get('title', default_title)
                                            lyric = song.get('lyric', "")
                                            valid, _ = validate_song_data(artist, title, lyric)
                                            if valid:
                                                add_song(artist, title, lyric)
                                                success_count += 1
                            
                            elif file_type == 'txt':
                                songs = []
                                current_song = {'artist': '', 'title': '', 'lyric': []}
                                for line in content.split('\n'):
                                    line = line.strip()
                                    if line.startswith('歌手：') or line.startswith('歌手:'):
                                        current_song['artist'] = line[3:].strip()
                                    elif line.startswith('歌名：') or line.startswith('歌名:'):
                                        current_song['title'] = line[3:].strip()
                                    elif line:
                                        current_song['lyric'].append(line)
                                    else:
                                        if current_song['artist'] and current_song['title']:
                                            songs.append(current_song)
                                        current_song = {'artist': '', 'title': '', 'lyric': []}
                                
                                if current_song['artist'] and current_song['title']:
                                    songs.append(current_song)
                                
                                for song in songs:
                                    artist = song.get('artist', "未知歌手")
                                    title = song.get('title', default_title)
                                    lyric = '\n'.join(song.get('lyric', []))
                                    valid, _ = validate_song_data(artist, title, lyric)
                                    if valid:
                                        add_song(artist, title, lyric)
                                        success_count += 1
                        
                        except Exception:
                            continue
                
                st.success(f"🎉 批量导入完成！成功导入 {success_count}/{total_files} 个文件")
                st.balloons()

            # 单个文件处理逻辑
            for i, uploaded_file in enumerate(uploaded_files, 1):
                try:
                    # 显示处理进度
                    st.write(f"### 正在处理文件 ({i}/{total_files}): {uploaded_file.name}")
                    
                    # 获取文件内容和类型
                    content = uploaded_file.getvalue().decode('utf-8')
                    file_type = uploaded_file.name.split('.')[-1].lower()
                    
                    # 从文件名提取歌曲名（去除.lrc扩展名）
                    filename = uploaded_file.name
                    default_title = filename[:-4] if filename.lower().endswith('.lrc') else filename
                    default_title = re.sub(r'[\\/*?:"<>|]', "", default_title).strip()
                    
                    # 显示原始内容供参考
                    with st.expander("查看原始文件内容"):
                        st.text(content[:500] + ("..." if len(content) > 500 else ""))
                    
                    # 根据文件类型处理
                    if file_type == 'lrc':
                        # 解析LRC文件
                        with st.spinner(f"正在解析 {uploaded_file.name}..."):
                            lrc_data = parse_lrc(content)
                        
                        # 检查解析结果
                        if 'error' in lrc_data:
                            st.error(f"❌ 解析LRC文件失败: {lrc_data['error']}")
                            continue
                        
                        # 如果没有解析到歌曲名，使用文件名
                        if lrc_data.get('title') == "未知歌曲":
                            lrc_data['title'] = default_title
                            st.info(f"⚠️ 未从文件内容中解析到歌曲名，将使用文件名作为歌曲名: {default_title}")
                        
                        # 创建编辑表单 - 使用唯一的表单key
                        with st.form(key=f"lrc_form_{i}_{uploaded_file.name.replace('.', '_')}"):
                            # 显示并允许编辑元数据
                            col1_inner, col2_inner = st.columns(2)
                            with col1_inner:
                                artist = st.text_input(
                                    "歌手名",
                                    value=lrc_data['artist'],
                                    key=f"artist_{i}_{uploaded_file.name}",
                                    help="如果自动识别的歌手名不正确，请手动修改"
                                )
                            with col2_inner:
                                title = st.text_input(
                                    "歌曲名",
                                    value=lrc_data['title'],
                                    key=f"title_{i}_{uploaded_file.name}",
                                    help=f"如果自动识别的歌曲名不正确，请手动修改{' (当前使用文件名作为歌曲名)' if lrc_data.get('title') == default_title else ''}"
                                )
                            
                            # 显示并允许编辑歌词
                            lyrics = st.text_area(
                                "歌词内容",
                                value=lrc_data['lyric'],
                                height=300,
                                key=f"lyrics_{i}_{uploaded_file.name}",
                                help="可以直接编辑歌词内容"
                            )
                            
                            # 提交按钮
                            submitted = st.form_submit_button("确认导入")
                            
                            if submitted:
                                # 验证数据
                                valid, error_msg = validate_song_data(
                                    artist,
                                    title,
                                    lyrics
                                )
                                
                                if valid:
                                    add_song(artist, title, lyrics)
                                    st.success(f"✅ 成功导入歌曲: {title}")
                                    success_count += 1
                                else:
                                    st.error(f"❌ 数据验证失败: {error_msg}")
                    
                    elif file_type == 'json':
                        try:
                            data = json.loads(content)
                            if isinstance(data, list):
                                # 批量导入多首歌曲
                                file_success = 0
                                for song in data:
                                    try:
                                        if all(k in song for k in ['artist', 'title', 'lyric']):
                                            valid, _ = validate_song_data(
                                                song['artist'],
                                                song['title'],
                                                song['lyric']
                                            )
                                            if valid:
                                                add_song(song['artist'], song['title'], song['lyric'])
                                                file_success += 1
                                    except Exception as e:
                                        st.error(f"导入歌曲失败: {str(e)}")
                                
                                success_count += 1 if file_success > 0 else 0
                                st.success(f"✅ 文件 {uploaded_file.name} 导入完成 (成功 {file_success}/{len(data)} 首)")
                            else:
                                st.error("JSON文件格式不正确，应包含歌曲数组")
                        except json.JSONDecodeError:
                            st.error(f"❌ 文件 {uploaded_file.name} 不是有效的JSON格式")
                        except Exception as e:
                            st.error(f"❌ 处理文件 {uploaded_file.name} 时出错: {str(e)}")
                    
                    elif file_type == 'txt':
                        try:
                            # 处理TXT文件
                            songs = []
                            current_song = {'artist': '', 'title': '', 'lyric': []}
                            
                            for line in content.split('\n'):
                                try:
                                    line = line.strip()
                                    if line.startswith('歌手：') or line.startswith('歌手:'):
                                        current_song['artist'] = line[3:].strip()
                                    elif line.startswith('歌名：') or line.startswith('歌名:'):
                                        current_song['title'] = line[3:].strip()
                                    elif line:
                                        current_song['lyric'].append(line)
                                    else:
                                        if current_song['artist'] and current_song['title']:
                                            songs.append(current_song)
                                        current_song = {'artist': '', 'title': '', 'lyric': []}
                                except Exception as e:
                                    st.error(f"解析行时出错: {line} - {str(e)}")
                            
                            # 添加最后一个歌曲
                            if current_song['artist'] and current_song['title']:
                                songs.append(current_song)
                            
                            # 导入解析的歌曲
                            file_success = 0
                            for song in songs:
                                try:
                                    valid, error_msg = validate_song_data(
                                        song['artist'],
                                        song['title'],
                                        '\n'.join(song['lyric'])
                                    )
                                    if valid:
                                        add_song(song['artist'], song['title'], '\n'.join(song['lyric']))
                                        file_success += 1
                                except Exception as e:
                                    st.error(f"导入歌曲失败: {song.get('title', '未知歌曲')} - {str(e)}")
                            
                            success_count += 1 if file_success > 0 else 0
                            st.success(f"✅ 文件 {uploaded_file.name} 导入完成 (成功 {file_success}/{len(songs)} 首)")
                        
                        except Exception as e:
                            st.error(f"❌ 处理TXT文件 {uploaded_file.name} 时出错: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ 读取文件 {uploaded_file.name} 失败: {str(e)}")
                    continue
            
            # 显示总体导入结果
            st.write("---")
            if success_count > 0:
                st.success(f"🎉 批量导入完成！成功处理 {success_count}/{total_files} 个文件")

# 数据导出部分 - 完全独立，不在任何form内
with col2:
    st.subheader("数据导出")
    
    if st.session_state['song_db']:
        # 导出选项
        export_format = st.selectbox(
            "导出格式",
            ["JSON", "TXT"],
            key="export_format"
        )
        
        # 生成导出数据
        if export_format == "JSON":
            json_data = export_to_json(st.session_state['song_db'])
            file_data = json_data
            file_name = "lyrics_data.json"
            mime_type = "application/json"
        else:  # TXT导出
            txt_data = ""
            for song in st.session_state['song_db']:
                txt_data += f"歌手：{song['artist']}\n"
                txt_data += f"歌名：{song['title']}\n"
                txt_data += f"{song['lyric']}\n\n"
            file_data = txt_data
            file_name = "lyrics_data.txt"
            mime_type = "text/plain"
        
        # 下载按钮 - 完全独立
        st.download_button(
            f"下载{export_format}文件",
            file_data,
            file_name,
            mime_type,
            use_container_width=True,
            key=f"{export_format.lower()}_download_btn"
        )
        
        # 数据统计
        st.write("### 数据统计")
        st.write(f"- 总歌曲数：{len(st.session_state['song_db'])}")
        st.write(f"- 歌手数量：{len(set(song['artist'] for song in st.session_state['song_db']))}")
        
        # 导入历史
        st.write("### 导入历史")
        if st.session_state['import_history']:
            for record in reversed(st.session_state['import_history'][-10:]):
                st.write(
                    f"- {record['timestamp'].strftime('%Y-%m-%d %H:%M')} - "
                    f"{record['details']}"
                )
    else:
        st.info("暂无可导出的数据")