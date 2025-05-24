import json
from collections import Counter

# 读取风格词典
def load_style_dict(style_dict_path='style_dict.json'):
    try:
        with open(style_dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载风格词典失败：{e}")
        return {}

# 风格分析函数
def classify_style(lyrics, style_dict):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    
    style_count = {style: 0 for style in style_dict}
    # 使用TF-IDF计算关键词权重，增加对中文的支持
    vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', max_features=500)
    docs = [' '.join(keywords) for keywords in style_dict.values()]
    tfidf_matrix = vectorizer.fit_transform(docs + [lyrics])
    feature_names = vectorizer.get_feature_names_out()
    
    # 计算每个风格的得分
    total_similarity = 0
    for i, style in enumerate(style_dict.keys()):
        style_vector = tfidf_matrix[i].toarray().flatten()
        lyrics_vector = tfidf_matrix[-1].toarray().flatten()
        # 使用余弦相似度计算风格与歌词的匹配度
        dot_product = np.dot(style_vector, lyrics_vector)
        norm_style = np.linalg.norm(style_vector)
        norm_lyrics = np.linalg.norm(lyrics_vector)
        if norm_style > 0 and norm_lyrics > 0:
            similarity = dot_product / (norm_style * norm_lyrics)
            style_count[style] = similarity
            total_similarity += similarity
        else:
            style_count[style] = 0
    
    # 归一化得分，计算每个风格的相对比例
    normalized_count = {style: score / total_similarity if total_similarity > 0 else 0 for style, score in style_count.items()}
    
    # 选择得分最高的风格作为主风格，强制选择一个风格，即使得分很低
    main_style = max(style_count, key=style_count.get) if style_count else list(style_dict.keys())[0]
    
    return main_style, normalized_count