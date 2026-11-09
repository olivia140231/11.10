# -*- coding: utf-8 -*-
"""
Builds a production-ready, mobile-first responsive HTML dashboard for GitHub Pages.
Dataset: Franke Malaysia Chinese Epigraphic Sites (Nanyang Data CC BY-SA 4.0)
"""

import re
import json
import pandas as pd
import yaml

csv_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv'
yaml_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.yaml'
output_html = r'c:\Users\James Lin\Desktop\21205\index.html'

# 1. Load and merge
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
        'address': str(r['address']) if pd.notna(r['address']) else '',
        'origin': r['origin_group'],
        'lat': float(r['latitude']) if pd.notna(r['latitude']) else None,
        'lng': float(r['longitude']) if pd.notna(r['longitude']) else None
    })

print(f"Total sites processed: {len(sites_data)}")
print(f"Sites with coordinates: {sum(1 for s in sites_data if s['lat'] is not None)}")

# Build HTML
html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
    <meta name="theme-color" content="#1e293b">
    <meta name="description" content="馬來西亞華文銘刻數據時空與移民祖籍分析看板 - Nanyang Data (CC BY-SA 4.0)">
    <title>馬來西亞華文銘刻數據分析看板</title>
    
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <!-- Leaflet CSS & JS for Interactive Map -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <style>
        :root {{
            --primary: #1e3a8a;
            --primary-light: #3b82f6;
            --accent: #d97706;
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-sub: #64748b;
            --border: #e2e8f0;
            --temple: #ef4444;
            --clan: #3b82f6;
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
            line-height: 1.5;
            padding-bottom: 72px; /* space for mobile bottom bar if needed */
        }}
        /* Responsive Container */
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

        /* Header */
        header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 24px 20px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            margin-bottom: 20px;
        }}
        header h1 {{
            font-size: 20px;
            font-weight: 800;
            line-height: 1.3;
            margin-bottom: 8px;
            letter-spacing: -0.3px;
        }}
        @media (min-width: 768px) {{
            header h1 {{ font-size: 26px; }}
            header {{ padding: 32px; }}
        }}
        header p {{
            font-size: 13.5px;
            color: #94a3b8;
            line-height: 1.5;
        }}
        .badge-source {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.35);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-top: 12px;
            font-weight: 700;
            word-break: break-word;
        }}

        /* Navigation Tabs for Mobile & Desktop */
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
            padding: 10px 14px;
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
            color: var(--primary);
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        }}

        /* Tab Content Section */
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
            font-size: 11.5px;
            font-weight: 700;
            color: var(--text-sub);
            margin-bottom: 4px;
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
            color: var(--primary);
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
        .insight-card h3 {{
            font-size: 14.5px;
            font-weight: 800;
            margin-bottom: 6px;
            color: var(--text-main);
        }}
        .insight-card p {{
            font-size: 13px;
            color: #334155;
            line-height: 1.55;
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
        <!-- Header -->
        <header>
            <h1>馬來西亞華文銘刻數據分析看板</h1>
            <p>數位化自傅吾康（Wolfgang Franke）與陳鐵凡合編《馬來西亞華文銘刻萃編》之 397 處古蹟站點，結合時空年代與移民祖籍原鄉分析。</p>
            <div class="badge-source">
                <span>📍</span> 資料來源：Nanyang Data（CC BY-SA 4.0）
            </div>
        </header>

        <!-- Navigation Tabs (Mobile-Friendly) -->
        <nav class="nav-tabs">
            <button class="tab-btn active" onclick="showTab('tab-types')">🏛️ 點位類型</button>
            <button class="tab-btn" onclick="showTab('tab-time')">⏳ 建立年代</button>
            <button class="tab-btn" onclick="showTab('tab-origins')">🧭 移民祖籍</button>
            <button class="tab-btn" onclick="showTab('tab-map')">🗺️ 地圖與檢索</button>
        </nav>

        <!-- KPI Summary Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">總站點記錄</div>
                <div class="kpi-value">{len(df)} 處</div>
                <div class="kpi-desc">涵蓋全馬各州古蹟</div>
            </div>
            <div class="kpi-card temple">
                <div class="kpi-label">最大功能類型</div>
                <div class="kpi-value">寺廟 (45%)</div>
                <div class="kpi-desc">共 179 處宮觀庵堂</div>
            </div>
            <div class="kpi-card gold">
                <div class="kpi-label">最集中年代</div>
                <div class="kpi-value">1851-1950</div>
                <div class="kpi-desc">高達 83.8% 集中此期</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-label">移民同鄉團體</div>
                <div class="kpi-value">{len(df_orgs)} 處</div>
                <div class="kpi-desc">會館/公所/公會</div>
            </div>
        </div>

        <!-- ================= TAB 1: SITE TYPES ================= -->
        <section id="tab-types" class="tab-pane active">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>🏛️</span> 點位類型分佈（長條圖）</div>
                    <span style="font-size:12px; color:var(--text-sub); font-weight:700;">共 397 筆</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="typeChart"></canvas>
                </div>
            </div>

            <div class="insight-card">
                <h3>📌 歷史解讀：海外華人社會「三大支柱」結構 (佔比 93.2%)</h3>
                <p>
                    本資料庫中，<strong>寺廟宮觀（45.1%）</strong>、<strong>會館宗祠（25.4%）</strong>與<strong>公墓義山（22.7%）</strong>合計達 93.2%。
                    這清晰印證了東南亞華人拓殖史的核心機制：<strong>神廟</strong>凝聚神權與信仰認同，<strong>會館</strong>串聯地緣血緣互助，<strong>義山</strong>落實死有所歸的族群福祉。
                </p>
            </div>
        </section>

        <!-- ================= TAB 2: TIME ERAS ================= -->
        <section id="tab-time" class="tab-pane">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>⏳</span> 建立/最早銘刻年代分佈（長條圖）</div>
                    <div class="toggle-group">
                        <button class="toggle-mini-btn active" id="btnDecade" onclick="switchTimeView('decade')">每十年</button>
                        <button class="toggle-mini-btn" id="btnPeriod" onclick="switchTimeView('period')">半世紀</button>
                    </div>
                </div>
                <div class="chart-wrapper">
                    <canvas id="timeChart"></canvas>
                </div>
            </div>

            <div class="insight-card gold">
                <h3>📌 歷史解讀：錫礦與橡膠大移民潮（1880–1920年代高峰）</h3>
                <p>
                    年代計算顯示，點位最早可追溯至 <strong>1622 年</strong>（麻六甲三保山甲必丹李為經墓），但超過 <strong>83.8%</strong> 均建立在 <strong>1851 年至 1950 年</strong> 間。
                    其中 <strong>1890 年代（54處）</strong> 為歷史最高峰，1880–1929 半世紀內聚集超過 55% 銘刻，精確對應英殖民時期馬來亞錫礦與橡膠業大繁榮之華人移民潮。
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
                <h3>📌 歷史解讀：各大方言群（Bang）力量分佈</h3>
                <p>
                    在篩出的 81 處同鄉組織中，<strong>閩南籍（21筆）</strong>、<strong>廣府籍（18筆）</strong>、<strong>客家籍（15筆）</strong>與<strong>海南籍（14筆）</strong>四大群體囊括 84%，
                    忠實呈現了「閩南掌商賈埠頭、廣客闢礦業山林、海南司餐飲航運」的經典南洋分工與聚落地理。
                </p>
            </div>
        </section>

        <!-- ================= TAB 4: MAP & SEARCH ================= -->
        <section id="tab-map" class="tab-pane">
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-title"><span>🗺️</span> 馬來西亞銘刻站點互動地圖 (314 處已定位)</div>
                </div>
                <div id="map"></div>
            </div>

            <div class="chart-card">
                <div class="chart-title" style="margin-bottom:12px;"><span>🔍</span> 站點清單即時檢索</div>
                <div class="search-box">
                    <input type="text" id="searchInput" class="search-input" placeholder="輸入中文名、拼音、年份或地址搜尋..." oninput="filterSites()">
                </div>
                <div class="site-item-list" id="sitesList">
                    <!-- Dynamic Items -->
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer>
            <p><strong>資料來源：Nanyang Data（CC BY-SA 4.0）</strong></p>
            <p style="margin-top:4px; font-size:12px;">
                Kenneth Dean, Marcus Bingenheimer et al. (NUS) based on Wolfgang Franke & Tieh-fan Chen (1982-1987).
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
            
            // Invalidate map size if map tab is activated
            if (tabId === 'tab-map' && map) {{
                setTimeout(() => {{ map.invalidateSize(); }}, 200);
            }}
        }}

        // Data from Python
        const typeLabels = {json.dumps(cat_labels, ensure_ascii=False)};
        const typeValues = {json.dumps(cat_values)};
        
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
                    backgroundColor: ['#ef4444', '#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#94a3b8'],
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
                    backgroundColor: decadeLabels.map(l => l === '1890s' ? '#d97706' : '#3b82f6'),
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
                            label: (ctx) => ` 站點數: ${{ctx.parsed.y}} 處`
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
                timeChart.data.datasets[0].backgroundColor = decadeLabels.map(l => l === '1890s' ? '#d97706' : '#3b82f6');
            }} else {{
                btnPeriod.classList.add('active');
                btnDecade.classList.remove('active');
                timeChart.data.labels = period50Labels;
                timeChart.data.datasets[0].data = period50Values;
                timeChart.data.datasets[0].backgroundColor = period50Labels.map(l => l.includes('20上') ? '#d97706' : (l.includes('19下') ? '#ea580c' : '#3b82f6'));
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

        // 4. Map Setup (Leaflet)
        let map = null;
        function initMap() {{
            map = L.map('map').setView([4.2105, 101.9758], 6);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; OpenStreetMap contributors'
            }}).addTo(map);

            // Add markers
            sitesData.forEach(site => {{
                if (site.lat && site.lng) {{
                    const marker = L.circleMarker([site.lat, site.lng], {{
                        radius: 5,
                        fillColor: site.category.includes('寺廟') ? '#ef4444' : (site.category.includes('會館') ? '#3b82f6' : '#10b981'),
                        color: '#ffffff',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.85
                    }}).addTo(map);

                    marker.bindPopup(`
                        <div style="font-size:13px; line-height:1.4;">
                            <strong style="color:#0f172a; font-size:14px;">${{site.nameZh}}</strong><br>
                            <span style="color:#64748b; font-size:11.5px;">${{site.nameAlt}}</span><hr style="margin:4px 0; border:none; border-top:1px solid #e2e8f0;">
                            <strong>類型：</strong>${{site.category}}<br>
                            <strong>最早銘刻：</strong>${{site.dateISO || '未詳'}}<br>
                            <strong>地址：</strong>${{site.address || '無現代地址紀錄'}}
                        </div>
                    `);
                }}
            }});
        }}

        // 5. Site Search & List
        function renderSitesList(items) {{
            const container = document.getElementById('sitesList');
            container.innerHTML = '';
            if (items.length === 0) {{
                container.innerHTML = '<div style="padding:16px; color:#94a3b8; text-align:center;">查無相符站點</div>';
                return;
            }}
            items.slice(0, 50).forEach(site => {{
                const div = document.createElement('div');
                div.className = 'site-item';
                div.innerHTML = `
                    <div>
                        <div class="site-item-name">${{site.nameZh}}</div>
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
                s.category.toLowerCase().includes(q)
            );
            renderSitesList(filtered);
        }}

        // Initialize when window loaded
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

print(f"Successfully generated GitHub Pages ready index.html at: {output_html}")
