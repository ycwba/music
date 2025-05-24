import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import os
import re

# 分词函数
def tokenize(text):
    return list(jieba.cut(text))

# 读取歌词文本（支持文件和直接文本）
def read_lyrics(files=None, text=None):
    lyrics_list = []
    if files:
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                lyrics_list.append(f.read())
    if text:
        lyrics_list.append(text)
    return lyrics_list

# TF-IDF关键词提取
def extract_keywords(lyrics_list, top_k=20):
    # 检查输入是否为空或只包含空字符串
    if not lyrics_list or all(not lyric.strip() for lyric in lyrics_list):
        return [[] for _ in lyrics_list]
        
    vectorizer = TfidfVectorizer(tokenizer=tokenize)
    tfidf = vectorizer.fit_transform(lyrics_list)
    keywords = []
    for i, row in enumerate(tfidf):
        row_data = row.toarray().flatten()
        indices = np.argsort(row_data)[::-1][:top_k]
        words = [vectorizer.get_feature_names_out()[idx] for idx in indices if row_data[idx] > 0]
        keywords.append(words)
    return keywords

# 生成词云图片
def generate_wordcloud(text, font_path='msyh.ttc', output_file=None, artist=None):
    # 生成词云前先过滤歌手等信息
    text = clean_lyrics(text, artist)
    wc = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    if output_file:
        fig.savefig(output_file, bbox_inches='tight')
    return fig

def clean_lyrics(text, artist=None):
    # 检查输入是否为空
    if not text or not isinstance(text, str):
        return "示例歌词"  # 返回一个默认文本，避免后续处理出错
    
    # 过滤掉包含特定关键词的整行
    ignore_fields = ["作词", "作曲", "-", "(Live)", "(", ")", "曲", "词", "编曲", 
                    "录音室", "录音", "混音", "制作", "监制", "演唱", "歌手", 
                    "Artist", "纯音乐", "无歌词", "Instrumental"]
    if artist and isinstance(artist, str):
        ignore_fields.append(artist)
    
    lines = text.splitlines()
    filtered_lines = []
    for line in lines:
        # 整行包含无关信息则过滤
        if any(field in line for field in ignore_fields):
            continue
        # 过滤空行
        if line.strip():
            filtered_lines.append(line)
    
    # 如果过滤后没有内容，返回默认文本
    if not filtered_lines:
        return "示例歌词"
    
    text = '\n'.join(filtered_lines)
    
    # 去除歌词时间编码 [00:00.00]
    text = re.sub(r'\[\d{2}:\d{2}\.\d{2,}\]', '', text)
    
    # 去除其他常见的无关字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)  # 保留中文、英文、数字和空格
    
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    
    result = text.strip()
    return result if result else "示例歌词"