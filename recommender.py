import re

def parse_user_query(query):
    """
    解析用户输入，提取风格、歌手及任意关键词
    返回: {'style': xxx, 'artist': xxx, 'keywords': [kw1, kw2, ...]}
    """
    style = None
    artist = None
    # 假设风格词都在 style_dict.json 里
    import json
    try:
        with open('style_dict.json', 'r', encoding='utf-8') as f:
            style_dict = json.load(f)
    except Exception as e:
        print(f"加载风格词典失败：{e}")
        style_dict = {}
    for s in style_dict.keys():
        if s in query:
            style = s
            break
    # 简单正则匹配"xxx的歌"
    m = re.search(r'(\w+)的歌', query)
    if m:
        artist = m.group(1)
    # 提取所有非风格、非歌手的关键词
    # 去除风格、歌手词后，按空格/逗号/顿号/等分词
    clean_query = query
    if style:
        clean_query = clean_query.replace(style, '')
    if artist:
        clean_query = clean_query.replace(artist + '的歌', '')
    # 分词（简单按空格、逗号、顿号、和、与等）
    keywords = re.split(r'[ ,，、和与]', clean_query)
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    return {'style': style, 'artist': artist, 'keywords': keywords}

# 推荐函数
def recommend(lyrics_db, user_query):
    """
    lyrics_db: [{"artist": , "title": , "lyrics": , "style": }]
    user_query: 用户输入
    返回推荐的歌曲列表
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    cond = parse_user_query(user_query)
    results = []
    filtered_db = []
    
    # 风格和歌手过滤
    for item in lyrics_db:
        if cond['style'] and item.get('style') != cond['style']:
            continue
        if cond['artist'] and cond['artist'] not in item.get('artist', ''):
            continue
        filtered_db.append(item)
    
    if not filtered_db:
        return []
    
    # 使用TF-IDF计算语义相似性
    vectorizer = TfidfVectorizer()
    lyrics_texts = [item['lyrics'] for item in filtered_db]
    query_text = ' '.join(cond['keywords']) if cond['keywords'] else user_query
    tfidf_matrix = vectorizer.fit_transform(lyrics_texts + [query_text])
    
    # 计算余弦相似度
    similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
    
    for idx, item in enumerate(filtered_db):
        item = dict(item)  # 拷贝，避免污染原数据
        item['match_count'] = similarities[idx]
        results.append(item)
    
    # 按相似度降序排序
    results.sort(key=lambda x: x.get('match_count', 0), reverse=True)
    return results[:10]  # 最多推荐10首

def get_similar_songs(base_song, song_db, n_recommendations=5, consider_style=True):
    """
    基于歌曲内容推荐相似歌曲
    
    参数:
    - base_song: 基准歌曲字典，包含'artist', 'title', 'lyric'等字段
    - song_db: 歌曲数据库列表
    - n_recommendations: 推荐数量
    - consider_style: 是否考虑歌曲风格
    
    返回:
    推荐歌曲列表
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    # 过滤掉基准歌曲本身
    filtered_db = [song for song in song_db if song['id'] != base_song['id']]
    
    if not filtered_db:
        return []
    
    # 准备歌词文本
    lyrics_texts = [song['lyric'] for song in filtered_db]
    lyrics_texts.append(base_song['lyric'])  # 添加基准歌曲
    
    # 计算TF-IDF向量
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(lyrics_texts)
    
    # 计算余弦相似度
    similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
    
    # 为每首歌计算综合得分
    results = []
    for idx, song in enumerate(filtered_db):
        score = similarities[idx]
        
        # 如果考虑风格，对相同风格的歌曲加权
        if consider_style and 'style' in base_song and 'style' in song:
            if base_song['style'] == song['style']:
                score *= 1.2  # 相同风格的歌曲得分提高20%
        
        results.append({
            'song': song,
            'score': score
        })
    
    # 按得分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 返回推荐结果
    return [item['song'] for item in results[:n_recommendations]]
    """
    lyrics_db: [{"artist": , "title": , "lyrics": , "style": }]
    user_query: 用户输入
    返回推荐的歌曲列表
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    cond = parse_user_query(user_query)
    results = []
    filtered_db = []
    
    # 风格和歌手过滤
    for item in lyrics_db:
        if cond['style'] and item.get('style') != cond['style']:
            continue
        if cond['artist'] and cond['artist'] not in item.get('artist', ''):
            continue
        filtered_db.append(item)
    
    if not filtered_db:
        return []
    
    # 使用TF-IDF计算语义相似性
    vectorizer = TfidfVectorizer()
    lyrics_texts = [item['lyrics'] for item in filtered_db]
    query_text = ' '.join(cond['keywords']) if cond['keywords'] else user_query
    tfidf_matrix = vectorizer.fit_transform(lyrics_texts + [query_text])
    
    # 计算余弦相似度
    similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
    
    for idx, item in enumerate(filtered_db):
        item = dict(item)  # 拷贝，避免污染原数据
        item['match_count'] = similarities[idx]
        results.append(item)
    
    # 按相似度降序排序
    results.sort(key=lambda x: x.get('match_count', 0), reverse=True)
    return results[:10]  # 最多推荐10首