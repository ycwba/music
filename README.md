# Music Lyrics NLP 项目

## 功能简介
- 支持批量或单个上传.lrc/文本歌词文件，或直接输入歌词文本
- 提取TF-IDF关键词，生成词频词云
- 结合风格词典自动判断歌曲风格
- 统计歌手创作倾向
- 可视化展示分析结果
- 支持自然语言推荐歌曲

## 依赖安装
```bash
pip install -r requirements.txt
```

## 启动方法
```bash
streamlit run main.py
```

## 目录结构
- main.py：主界面与调度
- lyrics_analyzer.py：歌词分析
- style_classifier.py：风格判断
- artist_stats.py：歌手倾向统计
- recommender.py：推荐系统
- style_dict.json：风格关键词词典 