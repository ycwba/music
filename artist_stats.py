from collections import defaultdict, Counter
from style_classifier import classify_style, load_style_dict
from lyrics_analyzer import extract_keywords

# 歌手倾向统计
def artist_statistics(artist_lyrics_dict, style_dict):
    """
    artist_lyrics_dict: {artist: [歌词1, 歌词2, ...]}
    style_dict: 风格词典
    返回：每位歌手的风格分布和关键词分布
    """
    from collections import Counter
    from statistics import mean, stdev
    
    artist_stats = {}
    for artist, lyrics_list in artist_lyrics_dict.items():
        all_keywords = []
        song_styles = []
        style_distributions = []
        for lyrics in lyrics_list:
            if lyrics.strip():  # 确保歌词不为空
                main_style, style_count = classify_style(lyrics, style_dict)
                song_styles.append(main_style)  # 记录每首歌的主要风格
                style_distributions.append(style_count)  # 记录每首歌的风格分布
                # 提取关键词
                keywords = extract_keywords([lyrics], top_k=10)[0]
                all_keywords.extend(keywords)
        keyword_counter = Counter(all_keywords)
        
        # 计算歌手整体风格分布：基于每首歌风格分布的平均值
        style_proportions = {style: 0 for style in style_dict}
        total_songs = len(style_distributions)
        if total_songs > 0:
            for style in style_dict:
                style_proportions[style] = round(mean(dist[style] for dist in style_distributions) * 100, 2)
        
        # 计算主要风格和次要风格
        sorted_styles = sorted(style_proportions.items(), key=lambda x: x[1], reverse=True)
        primary_style = sorted_styles[0][0] if sorted_styles and sorted_styles[0][1] > 0 else "未知"
        secondary_style = sorted_styles[1][0] if len(sorted_styles) > 1 and sorted_styles[1][1] > 0 else "无"
        
        # 计算风格多样性指标（基于风格分布的标准差）
        diversity = 0
        if total_songs > 1:
            style_values = [style_proportions[style] for style in style_dict if style_proportions[style] > 0]
            diversity = round(stdev(style_values) if len(style_values) > 1 else 0, 2)
        
        artist_stats[artist] = {
            'style_distribution': style_proportions,
            'primary_style': primary_style,
            'secondary_style': secondary_style,
            'style_diversity': diversity,
            'top_keywords': keyword_counter.most_common(20)
        }
    return artist_stats