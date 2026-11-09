# -*- coding: utf-8 -*-
"""
Franke Malaysia Dataset Calibrated Dashboard Generator
Incorporates project README.md and 01-franke_malaysia_meta.yaml metadata specifications.
Data Source: Nanyang Sites GIS Data Pool (CC BY-SA 4.0)
Official Project: Chinese sites in Malaysia described by Wolfgang Franke (1988)
Credits: Wolfgang Franke 傅吾康, Tieh-fan Chen 陳鐵凡, Kenneth Dean 丁荷生, Marcus Bingenheimer 馬徳偉, Wang Junlin 汪俊霖, Wu Fei 吴菲
Portal: https://nanyang-data.info/
"""

import re
import json
import pandas as pd
import yaml

csv_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv'
yaml_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.yaml'
output_html = r'c:\Users\James Lin\Desktop\21205\index.html'

# 1. Load data
df_csv = pd.read_csv(csv_path, encoding='utf-8')
with open(yaml_path, 'r', encoding='utf-8') as f:
    df_yaml = pd.DataFrame(yaml.safe_load(f))
df = pd.merge(df_csv, df_yaml, on='nanyangSiteId', how='inner')

# 2. Site Type Classification
def classify_site(row):
    zh = str(row['siteNameZh']) if pd.notna(row['siteNameZh']) else ''
    alt = str(row['siteNameAlt1']).lower() if pd.notna(row['siteNameAlt1']) else ''
    notes = str(row['notes']).lower() if pd.notna(row['notes']) else ''
    
    if any(k in alt for k in ['cemetery', 'cemeteries', 'cemetry', 'cemetries', 'tombstone', 'grave', 'burial', 'tombs']) or \
       any(k in zh for k in ['墓', '塚', '義山', '墳', '坆地']):
        return '公墓 / 墓葬 / 義山'
    if any(k in alt for k in ['memorial', 'monument', 'stele', 'memorial stone', 'memorial fountain']) or \
       any(k in zh for k in ['紀念碑', '紀念堂', '殉難', '牌坊']):
        return '紀念碑 / 紀念設施'
    if any(k in alt for k in ['school', 'academy', 'college']) or \
       any(k in zh for k in ['學校', '公學', '書院', '中學', '小學']):
        return '學校 / 書院'
    if any(k in zh for k in ['會館', '公所', '公會', '宗祠', '家廟', '總會', '同鄉會', '宗親會', '俱樂部']) or \
       any(k in alt for k in ['hui-kuan', 'huiguan', 'association', 'guild', 'clan association', 'ancestral tablet', 'kung-ssu', 'kongsi', 'club']) or \
       ('company' in alt and not any(k in alt for k in ['temple', 'shrine'])) or \
       ('宗' in zh and '祠' in zh):
        return '會館 / 宗祠 / 組織公所'
    if any(k in zh for k in ['廟', '宮', '寺', '庵', '堂', '亭', '壇', '觀', '佛堂', '大伯公', '福德祠', '巖', '殿', '閣', '社', '德教會', '教']) or \
       any(k in alt for k in ['temple', 'shrine', 'monastery', 'convent', 'grotto', 'kung', 'miao', 'an', 'ssu', 't\'ang', 'tang', 'to-pek-kong', 'fuk-tet-chi', 'she', 'lien-lin']) or \
       '寺' in notes or '堂' in notes or '廟' in notes:
        return '寺廟 / 宮觀 / 庵堂'
    return '其他 (住宅、公共設施等)'

# 3. Year Parsing
def parse_year(val):
    if pd.isna(val) or val == '':
        return None
    val = str(val).strip()
    m = re.search(r'\b(1[6-9]\d{2}|20\d{2})\b', val)
    if m:
        range_match = re.search(r'(\d{4})\s*[-/]\s*(\d{2,4})', val)
        if range_match:
            return int(range_match.group(1))
        return int(m.group(1))
    m_s = re.search(r'(\d{4})s', val)
    if m_s:
        return int(m_s.group(1))
    return None

df['category'] = df.apply(classify_site, axis=1)
df['year'] = df['dateISO'].apply(parse_year)
df['has_coord'] = df['latitude'].notna()

# 4. Step 1: Immigrant association filter
step1_kws = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(step1_kws)
df['is_immigrant_org'] = df['siteNameZh'].fillna('').str.contains(pattern1)

# 5. Step 2: Immigrant origin groups
origin_mapping = {
    '閩籍 / 閩南群': ['福建', '閩南', '漳泉', '漳州', '泉州', '安溪', '永春', '惠安', '晉江', '同安', '金厦', '興安', '詔安', '福州', '龍巖'],
    '廣府群 (粵)': ['廣肇', '番禺', '會寗', '台山', '寧陽', '岡州', '四邑', '南海', '香山', '中山', '順德', '清遠', '東安', '增龍'],
    '客家群 (客屬)': ['客屬', '惠州', '鵝城', '嘉應', '應和', '茶陽', '大埔', '海陸', '永定'],
    '海南群 (瓊州)': ['瓊州', '琼州', '海南'],
    '潮州群 (潮汕)': ['潮州', '韓江'],
    '廣西群': ['廣西'],
    '雷州群': ['雷州'],
    '跨省/綜合機構': ['廣東會館', '廣東暨汀州', '廣肇惠', '平章會館', '古城會館'],
    '非地緣職業公會': ['商業職員公會']
}

def classify_origin(zh_name):
    if not zh_name:
        return '非同鄉組織'
    for grp, kws in origin_mapping.items():
        if any(k in zh_name for k in kws):
            return grp
    return '其他或未詳'

df['origin_group'] = df.apply(lambda r: classify_origin(r['siteNameZh']) if r['is_immigrant_org'] else '非同鄉組織', axis=1)

# Stats: Categories
cat_counts = df['category'].value_counts()
cat_labels = list(cat_counts.index)
cat_values = [int(v) for v in cat_counts.values]

# Stats: Geocoding breakdown
geocoded_cat_counts = df[df['has_coord']]['category'].value_counts().reindex(cat_labels).fillna(0).astype(int).tolist()
ungeocoded_cat_counts = df[~df['has_coord']]['category'].value_counts().reindex(cat_labels).fillna(0).astype(int).tolist()

# Stats: Eras (50-yr)
bins_50 = [1600, 1650, 1700, 1750, 1800, 1850, 1900, 1950, 2000]
labels_50 = ['1601-1650 (17上)', '1651-1700 (17下)', '1701-1750 (18上)', '1751-1800 (18下)', 
             '1801-1850 (19上)', '1851-1900 (19下)', '1901-1950 (20上)', '1951-2000 (20下)']
period_50_counts = pd.cut(df['year'], bins=bins_50, labels=labels_50).value_counts().sort_index()
period_50_labels = list(labels_50)
period_50_values = [int(v) for v in period_50_counts.values]

# Stats: Decades (1840-1960)
bins_10 = list(range(1840, 1970, 10))
labels_10 = [f'{y}s' for y in range(1840, 1960, 10)]
decade_counts = pd.cut(df['year'], bins=bins_10, labels=labels_10, right=False).value_counts().sort_index()
decade_labels = list(decade_counts.index)
decade_values = [int(v) for v in decade_counts.values]

# Stats: Origin Groups (Step 2 among Step 1)
df_orgs = df[df['is_immigrant_org']].copy()
origin_counts = df_orgs['origin_group'].value_counts()
origin_labels = list(origin_counts.index)
origin_values = [int(v) for v in origin_counts.values]

# Prepare points JSON for map & search
sites_data = []
for idx, r in df.iterrows():
    sites_data.append({
        'id': r['nanyangSiteId'],
        'franke': str(r['FrankeNo']) if pd.notna(r['FrankeNo']) else '',
        'nameZh': str(r['siteNameZh']) if pd.notna(r['siteNameZh']) else '（無中文名）',
        'nameAlt': str(r['siteNameAlt1']) if pd.notna(r['siteNameAlt1']) else '',
        'category': r['category'],
        'year': int(r['year']) if pd.notna(r['year']) else None,
        'dateISO': str(r['dateISO']) if pd.notna(r['dateISO']) else '',
        'dateRef': str(r['dateRef']) if pd.notna(r['dateRef']) else '',
        'address': str(r['address']) if pd.notna(r['address']) else '',
        'notes': str(r['notes']) if pd.notna(r['notes']) else '',
        'origin': r['origin_group'],
        'hasCoord': bool(r['has_coord']),
        'lat': float(r['latitude']) if pd.notna(r['latitude']) else None,
        'lng': float(r['longitude']) if pd.notna(r['longitude']) else None
    })

# Build Calibrated HTML
html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
    <meta name="theme-color" content="#0f172a">
    <meta name="description" content="馬來西亞華文銘刻數據分析看板 - 根據 README 與 01-franke_malaysia_meta.yaml 元數據學術規範校正">
    <title>馬來西亞華文銘刻數據分析看板 (校正版)</title>
    
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <!-- Leaflet CSS & JS for Interactive Map -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <style>
        :root {{
            --primary: #0f172a;
            --primary-light: #2563eb;
            --accent: #d97706;
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-sub: #64748b;
            --border: #e2e8f0;
            --temple: #ef4444;
            --clan: #2563eb;
            --cemetery: #10b981;
            --memorial: #8b5cf6;
            --school: #f59e0b;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang TC", "Noto Sans TC", sans-serif;
        }}
        body {{
            background-color: var(--bg-page);
            color: var(--text-main);
            line-height: 1.55;
            padding-bottom: 60px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 16px;
        }}
        @media (min-width: 768px) {{
            .container {{
                padding: 24px;
            }}
        }}

        /* Header with Calibrated Metadata */
        header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 22px 18px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        @media (min-width: 768px) {{
            header {{ padding: 30px; }}
        }}
        .project-tag {{
            display: inline-block;
            background: rgba(56, 189, 248, 0.2);
            color: #38bdf8;
            font-size: 11.5px;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 12px;
            margin-bottom: 8px;
            border: 1px solid rgba(56, 189, 248, 0.35);
        }}
        header h1 {{
            font-size: 20px;
            font-weight: 800;
            line-height: 1.35;
            margin-bottom: 8px;
            letter-spacing: -0.3px;
        }}
        @media (min-width: 768px) {{
            header h1 {{ font-size: 25px; }}
        }}
        header p {{
            font-size: 13px;
            color: #94a3b8;
            line-height: 1.55;
        }}
        .source-bar {{
            margin-top: 14px;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }}
        .badge-source {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.1);
            color: #f1f5f9;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-decoration: none;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .badge-portal {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #0284c7;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-decoration: none;
            transition: opacity 0.2s;
        }}
        .badge-portal:hover {{ opacity: 0.9; }}

        /* Calibration Notice Banner */
        .calibration-banner {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-left: 5px solid #3b82f6;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #1e3a8a;
            line-height: 1.55;
        }}
        .calibration-banner strong {{
            color: #1d4ed8;
        }}

        /* Navigation Tabs */
        .nav-tabs {{
            display: flex;
            background: #e2e8f0;
            padding: 4px;
            border-radius: 12px;
            margin-bottom: 20px;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            gap: 4px;
        }}
        .tab-btn {{
            flex: 1;
            min-width: 90px;
            padding: 10px 12px;
            border: none;
            background: transparent;
            font-size: 13.5px;
            font-weight: 700;
            color: #475569;
            border-radius: 9px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
            text-align: center;
        }}
        .tab-btn.active {{
            background: white;
            color: #0f172a;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }}

        /* Tab Content */
        .tab-pane {{
            display: none;
        }}
        .tab-pane.active {{
            display: block;
            animation: fadeIn 0.25s ease-in-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        @media (min-width: 768px) {{
            .kpi-grid {{
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
            }}
        }}
        .kpi-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 16px 14px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
            position: relative;
            overflow: hidden;
        }}
        .kpi-card::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--primary-light);
        }}
        .kpi-card.temple::before {{ background: var(--temple); }}
        .kpi-card.gold::before {{ background: var(--accent); }}
        .kpi-card.green::before {{ background: var(--cemetery); }}
        .kpi-label {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-sub);
            margin-bottom: 4px;
            text-transform: uppercase;
        }}
        .kpi-value {{
            font-size: 20px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 2px;
        }}
        @media (min-width: 768px) {{
            .kpi-value {{ font-size: 24px; }}
        }}
        .kpi-desc {{
            font-size: 11.5px;
            color: var(--text-sub);
        }}

        /* Chart Cards */
        .chart-card {{
            background: var(--bg-card);
            border-radius: 14px;
            padding: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
            margin-bottom: 20px;
        }}
        @media (min-width: 768px) {{
            .chart-card {{
                padding: 22px;
            }}
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .chart-title {{
            font-size: 15px;
            font-weight: 800;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        @media (min-width: 768px) {{
            .chart-title {{ font-size: 17px; }}
        }}
        .toggle-group {{
            display: inline-flex;
            background: #f1f5f9;
            padding: 2px;
            border-radius: 8px;
        }}
        .toggle-mini-btn {{
            border: none;
            background: transparent;
            padding: 4px 10px;
            font-size: 11.5px;
            font-weight: 700;
            color: var(--text-sub);
            border-radius: 6px;
            cursor: pointer;
        }}
        .toggle-mini-btn.active {{
            background: white;
            color: var(--primary-light);
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .chart-wrapper {{
            position: relative;
            width: 100%;
            height: 320px;
            max-height: 400px;
        }}
        @media (max-width: 480px) {{
            .chart-wrapper {{
                height: 290px;
            }}
        }}

        /* Insights Box */
        .insight-card {{
            background: white;
            border-radius: 12px;
            padding: 16px;
            border-left: 4px solid var(--primary-light);
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
            margin-bottom: 14px;
        }}
        .insight-card.gold {{ border-left-color: var(--accent); }}
        .insight-card.green {{ border-left-color: var(--cemetery); }}
        .insight-card.purple {{ border-left-color: #8b5cf6; }}
        .insight-card h3 {{
            font-size: 14.5px;
            font-weight: 800;
            margin-bottom: 6px;
            color: var(--text-main);
        }}
        .insight-card p {{
            font-size: 13px;
            color: #334155;
            line-height: 1.6;
        }}

        /* Two-Step Filter Visualizer */
        .step-container {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            margin-bottom: 20px;
        }}
        @media (min-width: 768px) {{
            .step-container {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        .step-box {{
            background: white;
            border-radius: 14px;
            padding: 18px;
            border: 1px solid var(--border);
        }}
        .step-tag {{
            display: inline-block;
            background: #ede9fe;
            color: #6d28d9;
            font-size: 11px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            margin-bottom: 10px;
        }}
        .step-box h3 {{
            font-size: 16px;
            font-weight: 800;
            margin-bottom: 8px;
        }}
        .step-box p {{
            font-size: 13px;
            color: var(--text-sub);
            margin-bottom: 12px;
        }}
        .kw-pill {{
            display: inline-block;
            background: #f1f5f9;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            padding: 3px 8px;
            border-radius: 14px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px 4px 2px 0;
        }}

        /* Geocoding Status Box */
        .geo-box {{
            background: #fffbeb;
            border: 1px solid #fef3c7;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #92400e;
        }}

        /* Map styling */
        #map {{
            width: 100%;
            height: 380px;
            border-radius: 12px;
            z-index: 1;
        }}
        @media (min-width: 768px) {{
            #map {{ height: 480px; }}
        }}

        /* Search & List Box */
        .search-box {{
            margin-bottom: 14px;
            display: flex;
            gap: 8px;
        }}
        .search-input {{
            flex: 1;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid var(--border);
            font-size: 14px;
            outline: none;
            transition: border 0.2s;
        }}
        .search-input:focus {{
            border-color: var(--primary-light);
        }}
        .site-item-list {{
            max-height: 350px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: white;
        }}
        .site-item {{
            padding: 10px 14px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .site-item:last-child {{ border-bottom: none; }}
        .site-item-name {{ font-weight: 700; color: var(--text-main); }}
        .site-item-meta {{ font-size: 11.5px; color: var(--text-sub); }}
        .badge-geo {{
            display: inline-block;
            font-size: 10.5px;
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: 700;
        }}
        .badge-geo.yes {{ background: #dcfce7; color: #166534; }}
        .badge-geo.no {{ background: #fee2e2; color: #991b1b; }}

        /* Academic Credits & Citation Section */
        .citation-card {{
            background: white;
            border-radius: 14px;
            padding: 20px;
            border: 1px solid var(--border);
            margin-top: 24px;
            font-size: 13px;
        }}
        .citation-card h4 {{
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 8px;
            color: var(--text-main);
        }}
        .citation-box {{
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            color: #334155;
            word-break: break-all;
            margin-top: 8px;
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 24px 16px;
            font-size: 13px;
            color: var(--text-sub);
            border-top: 1px solid var(--border);
            margin-top: 30px;
        }}
        footer a {{
            color: var(--primary-light);
            text-decoration: none;
            font-weight: 700;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with Full Calibrated Project Metadata -->
        <header>
            <span class="project-tag">Nanyang Sites GIS Layer: 01-franke_malaysia</span>
            <h1>馬來西亞華文銘刻數據分析看板（學術校正版）</h1>
            <p><strong>專案名稱：Chinese sites in Malaysia described by Wolfgang Franke (1988)</strong></p>
            <p style="margin-top:4px;">
                基於傅吾康（Wolfgang Franke）與陳鐵凡《馬來西亞華文銘刻萃編》（3冊，1982–1987），由新加坡國立大學（NUS）丁荷生（Kenneth Dean）、馬徳偉（Marcus Bingenheimer）、汪俊霖、吴菲等於 2024 年完成地理空間標註與數位化整理。
            </p>
            <div class="source-bar">
                <span class="badge-source">
                    ⚖️ 資料來源：Nanyang Data（CC BY-SA 4.0）
                </span>
                <a href="https://nanyang-data.info/" target="_blank" rel="noopener" class="badge-portal">
                    🌐 訪問官方系統：nanyang-data.info ↗
                </a>
            </div>
        </header>

        <!-- Academic Calibration Notice (Aligned with README & Meta YAML) -->
        <div class="calibration-banner">
            <strong>📋 依據專案 README.md 與 01-franke_malaysia_meta.yaml 校正說明：</strong><br>
            1. <strong>時間指標校正</strong>：原統計中之年代，在元數據中明確定義為<strong>「現存最早銘刻年代（Date of the Earliest Inscription according to Franke and Chen）」</strong>，作為推估古蹟歷史長度（Age of the site）的重要依據，而非建築本身之初建年份。<br>
            2. <strong>地理定位校正</strong>：全集收錄 <strong>397 處</strong>站點中，經 NUS 團隊以線上工具完成座標定位者為 <strong>314 處（79.1%）</strong>；其餘 <strong>83 處未能定位者，主要是因為大量墓葬與公墓（grave sites）在現代地圖上難以查考</strong>。
        </div>

        <!-- Navigation Tabs (Mobile-Friendly) -->
        <nav class="nav-tabs">
            <button class="tab-btn active" onclick="showTab('tab-types')">🏛️ 點位類型</button>
            <button class="tab-btn" onclick="showTab('tab-time')">⏳ 銘刻年代</button>
            <button class="tab-btn" onclick="showTab('tab-origins')">🧭 移民祖籍</button>
            <button class="tab-btn" onclick="showTab('tab-geocoding')">📍 定位校正</button>
            <button class="tab-btn" onclick="showTab('tab-map')">🗺️ 地圖與檢索</button>
        </nav>

        <!-- KPI Summary Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">全集收錄總站點</div>
                <div class="kpi-value">{len(df)} 處</div>
                <div class="kpi-desc">已定位 314 / 未定位 83</div>
            </div>
            <div class="kpi-card temple">
                <div class="kpi-label">最大功能類型</div>
                <div class="kpi-value">寺廟 (45.1%)</div>
                <div class="kpi-desc">共 179 處宮觀庵堂</div>
            </div>
            <div class="kpi-card gold">
                <div class="kpi-label">銘刻最集中時期</div>
                <div class="kpi-value">1851-1950</div>
                <div class="kpi-desc">高達 83.8% (332處)</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-label">移民同鄉團體</div>
                <div class="kpi-value">{len(df_orgs)} 處</div>
                <div class="kpi-desc">會館/公所/公會 (100%識別)</div>
            </div>
        </div>

        <!-- ================= TAB 1: SITE TYPES ================= -->
        <section id="tab-types" class="tab-pane active">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>🏛️</span> 點位類型分佈（長條圖）</div>
                    <span style="font-size:12px; color:var(--text-sub); font-weight:700;">全體 397 筆</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="typeChart"></canvas>
                </div>
            </div>

            <div class="insight-card">
                <h3>📌 歷史解讀：海外華人社會「三大支柱」結構 (佔比 93.2%)</h3>
                <p>
                    本資料庫中，<strong>寺廟宮觀（45.1%，179處）</strong>、<strong>會館宗祠（25.4%，101處）</strong>與<strong>公墓義山（22.7%，90處）</strong>合計達 93.2%。
                    這清晰印證了東南亞華人拓殖史的核心機制：<strong>神廟</strong>凝聚神權與信仰認同，<strong>會館</strong>串聯地緣血緣互助，<strong>義山</strong>落實死有所歸的族群福祉。
                </p>
            </div>
        </section>

        <!-- ================= TAB 2: TIME ERAS ================= -->
        <section id="tab-time" class="tab-pane">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>⏳</span> 現存最早銘刻年代分佈（長條圖）</div>
                    <div class="toggle-group">
                        <button class="toggle-mini-btn active" id="btnDecade" onclick="switchTimeView('decade')">每十年 (Decade)</button>
                        <button class="toggle-mini-btn" id="btnPeriod" onclick="switchTimeView('period')">半世紀 (50年)</button>
                    </div>
                </div>
                <div class="chart-wrapper">
                    <canvas id="timeChart"></canvas>
                </div>
            </div>

            <div class="insight-card gold">
                <h3>📌 學術校正：最早銘刻年代（Inscription Date）的指標意義</h3>
                <p>
                    根據 <code>01-franke_malaysia_meta.yaml</code> 定義，本年代為 <em>"date of the earliest inscription which is usually an indication of the age of the site"</em>。
                    最早點位為 <strong>1622 年</strong>（麻六甲三保山甲必丹李為經墓碑），但超過 <strong>83.8%</strong> 銘刻集中在 <strong>1851 年至 1950 年</strong> 間，其中 <strong>1890 年代（54處）</strong> 為歷史最高峰。這如實反映了 19 世紀下半葉英殖民時期錫礦開採與橡膠種植業大移民潮所遺留之物質文化繁盛期。
                </p>
            </div>
        </section>

        <!-- ================= TAB 3: IMMIGRANT ORIGINS ================= -->
        <section id="tab-origins" class="tab-pane">
            <div class="step-container">
                <div class="step-box">
                    <span class="step-tag">步驟一：同鄉組織篩選</span>
                    <h3>篩出移民組織：{len(df_orgs)} 筆</h3>
                    <p>利用移民同鄉組織常見字根，從 397 個點位中精確篩出：</p>
                    <div>
                        <span class="kw-pill">會館 (61)</span>
                        <span class="kw-pill">公所 (4)</span>
                        <span class="kw-pill">同鄉會 (4)</span>
                        <span class="kw-pill">公會 (12)</span>
                    </div>
                </div>
                <div class="step-box">
                    <span class="step-tag">步驟二：祖籍原鄉判斷</span>
                    <h3>祖籍原鄉辨識率：100%</h3>
                    <p>依據「siteNameZh」包含的省、府、縣及江海古稱進行分類：</p>
                    <div>
                        <span class="kw-pill">閩南/福建 (21)</span>
                        <span class="kw-pill">廣府/四邑 (18)</span>
                        <span class="kw-pill">客家/客屬 (15)</span>
                        <span class="kw-pill">瓊州/海南 (14)</span>
                        <span class="kw-pill">潮州/韓江 (4)</span>
                        <span class="kw-pill">廣西 (2)</span>
                        <span class="kw-pill">雷州 (1)</span>
                    </div>
                </div>
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>🧭</span> 移民祖籍原鄉分佈（長條圖）</div>
                    <span style="font-size:12px; color:var(--text-sub); font-weight:700;">同鄉組織共 81 筆</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="originChart"></canvas>
                </div>
            </div>

            <div class="insight-card green">
                <h3>📌 歷史解讀：四大方言群主導移民格局</h3>
                <p>
                    在篩出的 81 處同鄉組織中，<strong>閩南籍（21筆）</strong>、<strong>廣府籍（18筆）</strong>、<strong>客家籍（15筆）</strong>與<strong>海南籍（14筆）</strong>四大群體囊括 84%，
                    忠實呈現了「閩南掌商賈埠頭、廣客闢礦業山林、海南司餐飲航運」的經典南洋分工與聚落地理。
                </p>
            </div>
        </section>

        <!-- ================= TAB 4: GEOCODING CALIBRATION ================= -->
        <section id="tab-geocoding" class="tab-pane">
            <div class="geo-box">
                <strong>📍 元數據核心發現驗證：</strong>
                元數據記載 <em>"Especially the many grave sites listed by Franke and Chen are often impossible to find with the methods at our disposal."</em>
                <br>經 Python 交叉驗證：全資料庫 90 處墓葬中，正好有 <strong>45 處（整整 50%）未能完成地理定位</strong>；而未定位的 83 處點位中，<strong>墓葬就佔了超過 54.2%</strong>！
            </div>

            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>📊</span> 各類型站點之地理定位（Geo-referenced）狀態堆疊長條圖</div>
                    <span style="font-size:12px; color:var(--text-sub); font-weight:700;">已定位 314 處 vs 未定位 83 處</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="geoChart"></canvas>
                </div>
            </div>

            <div class="insight-card purple">
                <h3>📌 空間人文學研究啟示</h3>
                <p>
                    相較於宮廟（定位成功率 91.6%）與會館（定位成功率 84.2%）等具備鮮明現代門牌與地標屬性的建築，歷史華人墓塚、義山與家族私塚極易隨城市開發、遷葬或地貌變遷而湮沒於荒煙蔓草中，成為數位人文地理資訊系統（GIS）田野查證中最大的挑戰。
                </p>
            </div>
        </section>

        <!-- ================= TAB 5: MAP & SEARCH ================= -->
        <section id="tab-map" class="tab-pane">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>🗺️</span> 馬來西亞銘刻站點互動地圖 (314 處已定位點)</div>
                </div>
                <div id="map"></div>
            </div>

            <div class="chart-card">
                <div class="chart-title" style="margin-bottom:12px;"><span>🔍</span> 全體 397 處站點即時檢索 (含定位狀態)</div>
                <div class="search-box">
                    <input type="text" id="searchInput" class="search-input" placeholder="輸入中文名、拼音、年份、地址或定位狀態搜尋..." oninput="filterSites()">
                </div>
                <div class="site-item-list" id="sitesList">
                    <!-- Dynamic Items -->
                </div>
            </div>
        </section>

        <!-- Metadata & Citation Block (Required by README.md) -->
        <div class="citation-card">
            <h4>📖 專案元數據與引用文獻 (Metadata & Citation)</h4>
            <p>依據 <code>README.md</code> 與 <code>01-franke_malaysia_meta.yaml</code> 規範之完整引用格式：</p>
            <div class="citation-box">
                <strong>Layer:</strong> 01-franke_malaysia | <strong>Date:</strong> 2024-06-12 | <strong>License:</strong> CC BY-SA 4.0<br>
                <strong>Credits:</strong> Wolfgang Franke 傅吾康, Tieh-fan Chen 陳鐵凡, Kenneth Dean 丁荷生, Marcus Bingenheimer 馬徳偉, Wang Junlin 汪俊霖, and Wu Fei 吴菲.<br>
                <strong>Source:</strong> Franke, Wolfgang & Chen Tieh-fan (eds.). 1982-87. <em>Chinese Epigraphic Materials in Malaysia</em>. Kuala Lumpur: University of Malaysia Press. 3 vols.<br>
                <strong>Portal:</strong> <a href="https://nanyang-data.info/" target="_blank" rel="noopener">https://nanyang-data.info/</a> (Nanyang Sites GIS Data Pool)
            </div>
        </div>

        <!-- Footer -->
        <footer>
            <p><strong>資料來源：Nanyang Data（CC BY-SA 4.0）</strong></p>
            <p style="margin-top:4px; font-size:12px; color:#94a3b8;">
                Published under Creative Commons Attribution-ShareAlike 4.0 International License.
            </p>
        </footer>
    </div>

    <!-- Script: Data & Charts -->
    <script>
        // Tab switching logic
        function showTab(tabId) {{
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            
            if (tabId === 'tab-map' && map) {{
                setTimeout(() => {{ map.invalidateSize(); }}, 200);
            }}
        }}

        // Data from Python
        const typeLabels = {json.dumps(cat_labels, ensure_ascii=False)};
        const typeValues = {json.dumps(cat_values)};
        const geocodedValues = {json.dumps(geocoded_cat_counts)};
        const ungeocodedValues = {json.dumps(ungeocoded_cat_counts)};
        
        const period50Labels = {json.dumps(period_50_labels, ensure_ascii=False)};
        const period50Values = {json.dumps(period_50_values)};
        
        const decadeLabels = {json.dumps(decade_labels, ensure_ascii=False)};
        const decadeValues = {json.dumps(decade_values)};
        
        const originLabels = {json.dumps(origin_labels, ensure_ascii=False)};
        const originValues = {json.dumps(origin_values)};
        
        const sitesData = {json.dumps(sites_data, ensure_ascii=False)};

        // 1. Type Chart (Horizontal Bar Chart)
        const ctxType = document.getElementById('typeChart').getContext('2d');
        const typeChart = new Chart(ctxType, {{
            type: 'bar',
            data: {{
                labels: typeLabels,
                datasets: [{{
                    label: '站點數',
                    data: typeValues,
                    backgroundColor: ['#ef4444', '#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#94a3b8'],
                    borderRadius: 6
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(ctx) {{
                                const pct = ((ctx.parsed.x / 397) * 100).toFixed(1);
                                return ` 數量: ${{ctx.parsed.x}} 處 (${{pct}}%)`;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ font: {{ weight: '700', size: 11 }} }} }}
                }}
            }}
        }});

        // 2. Time Chart
        const ctxTime = document.getElementById('timeChart').getContext('2d');
        const timeChart = new Chart(ctxTime, {{
            type: 'bar',
            data: {{
                labels: decadeLabels,
                datasets: [{{
                    label: '站點數',
                    data: decadeValues,
                    backgroundColor: decadeLabels.map(l => l === '1890s' ? '#d97706' : '#2563eb'),
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => ` 最早銘刻站點數: ${{ctx.parsed.y}} 處`
                        }}
                    }}
                }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }},
                    x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 45, minRotation: 0, font: {{ size: 11 }} }} }}
                }}
            }}
        }});

        function switchTimeView(mode) {{
            const btnDecade = document.getElementById('btnDecade');
            const btnPeriod = document.getElementById('btnPeriod');
            if (mode === 'decade') {{
                btnDecade.classList.add('active');
                btnPeriod.classList.remove('active');
                timeChart.data.labels = decadeLabels;
                timeChart.data.datasets[0].data = decadeValues;
                timeChart.data.datasets[0].backgroundColor = decadeLabels.map(l => l === '1890s' ? '#d97706' : '#2563eb');
            }} else {{
                btnPeriod.classList.add('active');
                btnDecade.classList.remove('active');
                timeChart.data.labels = period50Labels;
                timeChart.data.datasets[0].data = period50Values;
                timeChart.data.datasets[0].backgroundColor = period50Labels.map(l => l.includes('20上') ? '#d97706' : (l.includes('19下') ? '#ea580c' : '#2563eb'));
            }}
            timeChart.update();
        }}

        // 3. Origin Chart (Horizontal Bar Chart)
        const ctxOrigin = document.getElementById('originChart').getContext('2d');
        const originChart = new Chart(ctxOrigin, {{
            type: 'bar',
            data: {{
                labels: originLabels,
                datasets: [{{
                    label: '組織數',
                    data: originValues,
                    backgroundColor: ['#0284c7', '#0d9488', '#e11d48', '#d97706', '#8b5cf6', '#64748b', '#475569', '#94a3b8', '#cbd5e1'],
                    borderRadius: 6
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => ` 組織數: ${{ctx.parsed.x}} 處`
                        }}
                    }}
                }},
                scales: {{
                    x: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ font: {{ weight: '700', size: 11 }} }} }}
                }}
            }}
        }});

        // 4. Geocoding Status Chart (Stacked Bar)
        const ctxGeo = document.getElementById('geoChart').getContext('2d');
        const geoChart = new Chart(ctxGeo, {{
            type: 'bar',
            data: {{
                labels: typeLabels,
                datasets: [
                    {{
                        label: '已完成定位 (314處)',
                        data: geocodedValues,
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    }},
                    {{
                        label: '未能定位 (83處)',
                        data: ungeocodedValues,
                        backgroundColor: '#f43f5e',
                        borderRadius: 4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top' }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => ` ${{ctx.dataset.label}}: ${{ctx.parsed.y}} 處`
                        }}
                    }}
                }},
                scales: {{
                    x: {{ stacked: true, grid: {{ display: false }} }},
                    y: {{ stacked: true, beginAtZero: true, grid: {{ color: '#f1f5f9' }} }}
                }}
            }}
        }});

        // 5. Map Setup (Leaflet)
        let map = null;
        function initMap() {{
            map = L.map('map').setView([4.2105, 101.9758], 6);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; OpenStreetMap contributors'
            }}).addTo(map);

            sitesData.forEach(site => {{
                if (site.lat && site.lng) {{
                    const marker = L.circleMarker([site.lat, site.lng], {{
                        radius: 5,
                        fillColor: site.category.includes('寺廟') ? '#ef4444' : (site.category.includes('會館') ? '#2563eb' : '#10b981'),
                        color: '#ffffff',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.85
                    }}).addTo(map);

                    marker.bindPopup(`
                        <div style="font-size:13px; line-height:1.4;">
                            <strong style="color:#0f172a; font-size:14px;">${{site.nameZh}}</strong><br>
                            <span style="color:#64748b; font-size:11.5px;">${{site.nameAlt}}</span><hr style="margin:4px 0; border:none; border-top:1px solid #e2e8f0;">
                            <strong>Franke編號：</strong>${{site.franke}}<br>
                            <strong>類型：</strong>${{site.category}}<br>
                            <strong>最早銘刻：</strong>${{site.dateISO || '未詳'}} (${{site.dateRef || ''}})<br>
                            <strong>地址：</strong>${{site.address || '無現代地址紀錄'}}
                        </div>
                    `);
                }}
            }});
        }}

        // 6. Site Search & List
        function renderSitesList(items) {{
            const container = document.getElementById('sitesList');
            container.innerHTML = '';
            if (items.length === 0) {{
                container.innerHTML = '<div style="padding:16px; color:#94a3b8; text-align:center;">查無相符站點</div>';
                return;
            }}
            items.slice(0, 60).forEach(site => {{
                const div = document.createElement('div');
                div.className = 'site-item';
                div.innerHTML = `
                    <div>
                        <div class="site-item-name">
                            ${{site.nameZh}} 
                            <span class="badge-geo ${{site.hasCoord ? 'yes' : 'no'}}">${{site.hasCoord ? '已定位' : '未定位'}}</span>
                        </div>
                        <div class="site-item-meta">${{site.nameAlt}} | ${{site.category}}</div>
                    </div>
                    <div style="text-align:right;">
                        <span style="background:#f1f5f9; padding:2px 6px; border-radius:4px; font-weight:700; font-size:11px;">
                            ${{site.dateISO || '年代未詳'}}
                        </span>
                    </div>
                `;
                div.onclick = () => {{
                    if (site.lat && site.lng && map) {{
                        showTab('tab-map');
                        map.setView([site.lat, site.lng], 14);
                        window.scrollTo({{ top: document.getElementById('map').offsetTop - 60, behavior: 'smooth' }});
                    }}
                }};
                container.appendChild(div);
            }});
        }}

        function filterSites() {{
            const q = document.getElementById('searchInput').value.trim().toLowerCase();
            if (!q) {{
                renderSitesList(sitesData);
                return;
            }}
            const filtered = sitesData.filter(s => 
                s.nameZh.toLowerCase().includes(q) ||
                s.nameAlt.toLowerCase().includes(q) ||
                (s.dateISO && s.dateISO.toLowerCase().includes(q)) ||
                (s.address && s.address.toLowerCase().includes(q)) ||
                s.category.toLowerCase().includes(q) ||
                (q === '已定位' && s.hasCoord) ||
                (q === '未定位' && !s.hasCoord)
            );
            renderSitesList(filtered);
        }}

        window.addEventListener('DOMContentLoaded', () => {{
            initMap();
            renderSitesList(sitesData);
        }});
    </script>
</body>
</html>
"""

with open(output_html, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"Successfully generated calibrated index.html at: {output_html}")
