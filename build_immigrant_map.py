# -*- coding: utf-8 -*-
"""
Builds a dedicated, color-coded interactive map for the screened immigrant associations.
Data Source: Nanyang Data (CC BY-SA 4.0)
Layer: 01-franke_malaysia
"""

import json
import pandas as pd
import yaml

csv_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv'
yaml_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.yaml'
output_map_html = r'c:\Users\James Lin\Desktop\21205\immigrant_map.html'
output_index_html = r'c:\Users\James Lin\Desktop\21205\index.html'

# 1. Load Data
df_csv = pd.read_csv(csv_path, encoding='utf-8')
with open(yaml_path, 'r', encoding='utf-8') as f:
    df_yaml = pd.DataFrame(yaml.safe_load(f))
df = pd.merge(df_csv, df_yaml, on='nanyangSiteId', how='inner')

# 2. Filter Step 1: Immigrant Associations (81 records)
step1_kws = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(step1_kws)
df_orgs = df[df['siteNameZh'].fillna('').str.contains(pattern1)].copy()

# 3. Classify Step 2: Immigrant Origin Groups
origin_meta = {
    '閩籍 / 閩南群': {
        'keywords': ['福建', '閩南', '漳泉', '漳州', '泉州', '安溪', '永春', '惠安', '晉江', '同安', '金厦', '興安', '詔安', '福州', '龍巖'],
        'color': '#2563eb', # Blue
        'desc': '泉州、漳州、福州、興化、永春、安溪等閩南閩東原鄉'
    },
    '廣府群 (粵)': {
        'keywords': ['廣肇', '番禺', '會寗', '台山', '寧陽', '岡州', '四邑', '南海', '香山', '中山', '順德', '清遠', '東安', '增龍'],
        'color': '#dc2626', # Red
        'desc': '廣州府、肇慶府及四邑（新會、台山、開平、恩平）等粵語區'
    },
    '客家群 (客屬)': {
        'keywords': ['客屬', '惠州', '鵝城', '嘉應', '應和', '茶陽', '大埔', '海陸', '永定'],
        'color': '#059669', # Emerald Green
        'desc': '惠州府、嘉應州（梅縣）、大埔茶陽及閩西汀州永定等客家聚落'
    },
    '海南群 (瓊州)': {
        'keywords': ['瓊州', '琼州', '海南'],
        'color': '#d97706', # Amber Orange
        'desc': '原廣東省瓊州府（海南島各縣）移民'
    },
    '潮州群 (潮汕)': {
        'keywords': ['潮州', '韓江'],
        'color': '#9333ea', # Purple
        'desc': '廣東省潮州府八邑及韓江水系原鄉'
    },
    '廣西群': {
        'keywords': ['廣西'],
        'color': '#0891b2', # Cyan
        'desc': '廣西省籍同鄉'
    },
    '雷州群': {
        'keywords': ['雷州'],
        'color': '#e11d48', # Rose Red
        'desc': '廣東省雷州半島籍移民（雷陽社）'
    },
    '跨省 / 綜合機構': {
        'keywords': ['廣東會館', '廣東暨汀州', '廣肇惠', '平章會館', '古城會館'],
        'color': '#475569', # Slate
        'desc': '跨省份或全省籍華人聯合會館與大會堂前身'
    },
    '非地緣職業公會': {
        'keywords': ['商業職員公會'],
        'color': '#94a3b8',
        'desc': '非原鄉性質之商業職場公會'
    }
}

def classify_origin(zh_name):
    for grp, meta in origin_meta.items():
        if any(k in zh_name for k in meta['keywords']):
            return grp
    return '其他或未詳'

df_orgs['origin_group'] = df_orgs['siteNameZh'].apply(classify_origin)
df_orgs['color'] = df_orgs['origin_group'].apply(lambda g: origin_meta.get(g, {}).get('color', '#64748b'))
df_orgs['has_coord'] = df_orgs['latitude'].notna()

# 4. Prepare JSON Payload for the Map
points_list = []
for idx, r in df_orgs.iterrows():
    points_list.append({
        'id': r['nanyangSiteId'],
        'frankeNo': str(r['FrankeNo']) if pd.notna(r['FrankeNo']) else '',
        'nameZh': str(r['siteNameZh']) if pd.notna(r['siteNameZh']) else '',
        'nameAlt': str(r['siteNameAlt1']) if pd.notna(r['siteNameAlt1']) else '',
        'origin': r['origin_group'],
        'color': r['color'],
        'hasCoord': bool(r['has_coord']),
        'lat': float(r['latitude']) if r['has_coord'] else None,
        'lng': float(r['longitude']) if r['has_coord'] else None,
        'dateISO': str(r['dateISO']) if pd.notna(r['dateISO']) else '',
        'dateRef': str(r['dateRef']) if pd.notna(r['dateRef']) else '',
        'address': str(r['address']) if pd.notna(r['address']) else '',
        'notes': str(r['notes']) if pd.notna(r['notes']) else ''
    })

# Group summary statistics
summary_stats = []
for grp, meta in origin_meta.items():
    if grp == '非地緣職業公會':
        continue
    sub = df_orgs[df_orgs['origin_group'] == grp]
    summary_stats.append({
        'name': grp,
        'color': meta['color'],
        'desc': meta['desc'],
        'total': len(sub),
        'geocoded': int(sub['has_coord'].sum())
    })

print(f"Total screened sites: {len(points_list)}")
print(f"Geocoded sites for map: {sum(1 for p in points_list if p['hasCoord'])}")

# Build Standalone Interactive Map HTML
html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
    <meta name="theme-color" content="#0f172a">
    <title>馬來西亞華人移民同鄉會館原鄉地圖 | Nanyang Data</title>
    
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #ffffff;
            --border: #e2e8f0;
            --text-main: #0f172a;
            --text-sub: #64748b;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang TC", "Noto Sans TC", sans-serif;
        }}
        body {{
            background: #f1f5f9;
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }}
        
        /* Top Navigation Header */
        header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }}
        .header-title-box h1 {{
            font-size: 17px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        @media (min-width: 768px) {{
            .header-title-box h1 {{ font-size: 20px; }}
        }}
        .header-title-box p {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 2px;
        }}
        .header-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .badge-source {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.35);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11.5px;
            font-weight: 700;
            text-decoration: none;
        }}
        .btn-toggle-panel {{
            background: rgba(255, 255, 255, 0.15);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12.5px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .btn-toggle-panel:hover {{ background: rgba(255, 255, 255, 0.25); }}

        /* Main App Body (Map + Sidebar) */
        .app-body {{
            flex: 1;
            display: flex;
            position: relative;
            overflow: hidden;
        }}
        
        /* Map Container */
        #map {{
            flex: 1;
            height: 100%;
            z-index: 10;
        }}
        
        /* Sidebar Drawer (Responsive for Mobile & Desktop) */
        .sidebar {{
            width: 380px;
            max-width: 100vw;
            background: white;
            border-left: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            z-index: 20;
            box-shadow: -4px 0 16px rgba(0,0,0,0.06);
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @media (max-width: 768px) {{
            .sidebar {{
                position: absolute;
                top: 0;
                bottom: 0;
                right: 0;
                width: 100%;
                transform: translateX(100%);
            }}
            .sidebar.mobile-open {{
                transform: translateX(0);
            }}
        }}

        .sidebar-header {{
            padding: 16px;
            border-bottom: 1px solid var(--border);
            background: #f8fafc;
        }}
        .sidebar-title {{
            font-size: 15px;
            font-weight: 800;
            color: var(--text-main);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .sidebar-close-btn {{
            display: none;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: var(--text-sub);
        }}
        @media (max-width: 768px) {{
            .sidebar-close-btn {{ display: block; }}
        }}

        /* Origin Group Filter Pills */
        .filter-section {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
            background: white;
        }}
        .filter-title {{
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            color: var(--text-sub);
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }}
        .filter-btn-reset {{
            font-size: 11.5px;
            color: #2563eb;
            background: none;
            border: none;
            cursor: pointer;
            font-weight: 700;
        }}
        .origin-chips {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            color: var(--text-main);
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .chip.active {{
            border-color: currentColor;
            background: #f1f5f9;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        .chip-dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
        }}
        .chip-count {{
            font-size: 10.5px;
            opacity: 0.75;
        }}

        /* Search input */
        .search-section {{
            padding: 10px 16px;
            background: white;
            border-bottom: 1px solid var(--border);
        }}
        .search-box {{
            display: flex;
            align-items: center;
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 6px 12px;
        }}
        .search-input {{
            border: none;
            background: transparent;
            font-size: 13px;
            width: 100%;
            outline: none;
            color: var(--text-main);
        }}

        /* Sites List */
        .sites-scroll {{
            flex: 1;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        }}
        .site-card {{
            padding: 12px 16px;
            border-bottom: 1px solid #f1f5f9;
            cursor: pointer;
            transition: background 0.15s;
        }}
        .site-card:hover {{
            background: #f8fafc;
        }}
        .site-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 3px;
        }}
        .site-card-name {{
            font-size: 14px;
            font-weight: 800;
            color: #0f172a;
        }}
        .site-card-tag {{
            font-size: 11px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            color: white;
            white-space: nowrap;
        }}
        .site-card-sub {{
            font-size: 12px;
            color: var(--text-sub);
            margin-bottom: 4px;
            line-height: 1.35;
        }}
        .site-card-foot {{
            display: flex;
            justify-content: space-between;
            font-size: 11.5px;
            color: #64748b;
        }}
        .badge-mapped {{
            color: #166534;
            font-weight: 700;
        }}
        .badge-unmapped {{
            color: #991b1b;
            font-weight: 700;
        }}

        /* Floating Legend Overlay on Map */
        .map-floating-legend {{
            position: absolute;
            bottom: 24px;
            left: 18px;
            background: rgba(255, 255, 255, 0.94);
            backdrop-filter: blur(8px);
            padding: 12px 14px;
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            border: 1px solid rgba(226, 232, 240, 0.8);
            z-index: 15;
            max-width: 290px;
            font-size: 12px;
            display: none;
        }}
        @media (min-width: 900px) {{
            .map-floating-legend {{ display: block; }}
        }}
        .legend-title {{
            font-weight: 800;
            font-size: 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 7px;
            margin-bottom: 4px;
            font-size: 11.5px;
            color: #334155;
        }}
        .legend-color {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        /* Custom Popup Styles */
        .leaflet-popup-content {{
            font-size: 13px;
            line-height: 1.5;
            min-width: 240px;
            max-width: 280px;
            margin: 12px 14px;
        }}
        .popup-title {{
            font-size: 15px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 2px;
        }}
        .popup-sub {{
            font-size: 12px;
            color: #64748b;
            margin-bottom: 6px;
        }}
        .popup-badge {{
            display: inline-block;
            padding: 2px 7px;
            border-radius: 4px;
            color: white;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .popup-detail {{
            border-top: 1px solid #e2e8f0;
            padding-top: 6px;
            margin-top: 6px;
            font-size: 12px;
            color: #334155;
        }}
        .popup-detail strong {{ color: #0f172a; }}
    </style>
</head>
<body>
    <!-- Top Header -->
    <header>
        <div class="header-title-box">
            <h1><span>🗺️</span> 馬來西亞華人移民同鄉會館原鄉分佈地圖</h1>
            <p>篩選自《馬來西亞華文銘刻萃編》81 處地緣同鄉團體，依祖籍原鄉色彩分類呈現</p>
        </div>
        <div class="header-actions">
            <span class="badge-source">
                ⚖️ 資料來源：Nanyang Data（CC BY-SA 4.0）
            </span>
            <button class="btn-toggle-panel" onclick="toggleSidebar()">
                <span>📋</span> 列表與篩選 (<span id="totalVisibleCount">71</span>)
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <div class="app-body">
        <!-- Leaflet Map Canvas -->
        <div id="map"></div>

        <!-- Floating Map Legend on Large Screens -->
        <div class="map-floating-legend">
            <div class="legend-title">
                <span>原鄉圖例（點擊上方切換）</span>
            </div>
            <div id="legendItemsList"></div>
            <div style="margin-top:6px; font-size:10.5px; color:#94a3b8; border-top:1px solid #f1f5f9; padding-top:4px;">
                共 71 處已標註座標，10 處無現代座標
            </div>
        </div>

        <!-- Sidebar Panel for Filtering & Site Inspecting -->
        <aside class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">
                    <span>🧭 祖籍原鄉分類篩選</span>
                    <button class="sidebar-close-btn" onclick="toggleSidebar()">✕</button>
                </div>
            </div>

            <!-- Origin Group Filter Section -->
            <div class="filter-section">
                <div class="filter-title">
                    <span>原鄉群別 (方言群)</span>
                    <button class="filter-btn-reset" onclick="resetFilters()">重設全部</button>
                </div>
                <div class="origin-chips" id="chipsContainer">
                    <!-- Dynamic Filter Chips -->
                </div>
            </div>

            <!-- Search box -->
            <div class="search-section">
                <div class="search-box">
                    <span style="margin-right:6px; color:#94a3b8;">🔍</span>
                    <input type="text" id="searchInput" class="search-input" placeholder="搜尋會館名稱、拼音或地址..." oninput="filterSites()">
                </div>
            </div>

            <!-- Filtered Sites Scrollable List -->
            <div class="sites-scroll" id="sitesList">
                <!-- Dynamic Site Cards -->
            </div>
        </aside>
    </div>

    <!-- Script: Map Rendering & Interactions -->
    <script>
        // Data injected from Python
        const pointsData = {json.dumps(points_list, ensure_ascii=False)};
        const summaryStats = {json.dumps(summary_stats, ensure_ascii=False)};

        let activeOrigins = new Set(summaryStats.map(s => s.name));
        let map = null;
        let markersLayer = null;

        // 1. Initialize Map
        function initMap() {{
            // Center roughly around West Malaysia
            map = L.map('map', {{
                zoomControl: true
            }}).setView([3.8, 102.0], 7);

            // Base map: CartoDB Positron / OSM for clean contrast
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a> | Data: Nanyang Data (CC BY-SA 4.0)',
                subdomains: 'abcd',
                maxZoom: 19
            }}).addTo(map);

            markersLayer = L.layerGroup().addTo(map);
            renderMarkers();
            renderLegend();
            renderChips();
            renderSitesList(pointsData);
        }}

        // 2. Render Circle Markers on Map
        function renderMarkers() {{
            markersLayer.clearLayers();
            const searchText = document.getElementById('searchInput') ? document.getElementById('searchInput').value.trim().toLowerCase() : '';

            let visibleCount = 0;
            pointsData.forEach(site => {{
                if (!site.hasCoord) return;
                if (!activeOrigins.has(site.origin)) return;
                if (searchText && !(
                    site.nameZh.toLowerCase().includes(searchText) ||
                    site.nameAlt.toLowerCase().includes(searchText) ||
                    site.address.toLowerCase().includes(searchText)
                )) return;

                visibleCount++;

                const marker = L.circleMarker([site.lat, site.lng], {{
                    radius: 7,
                    fillColor: site.color,
                    color: '#ffffff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9
                }});

                const popupHtml = `
                    <div>
                        <div class="popup-title">${{site.nameZh}}</div>
                        <div class="popup-sub">${{site.nameAlt}}</div>
                        <span class="popup-badge" style="background:${{site.color}}">${{site.origin}}</span>
                        <div class="popup-detail">
                            <strong>Franke編號：</strong>${{site.frankeNo}}<br>
                            <strong>現存最早銘刻：</strong>${{site.dateISO || '未詳'}} (${{site.dateRef || ''}})<br>
                            <strong>現代地址：</strong>${{site.address || '無現代地址紀錄'}}<br>
                            ${{site.notes ? `<strong>考證備註：</strong>${{site.notes}}` : ''}}
                        </div>
                    </div>
                `;

                marker.bindPopup(popupHtml);
                markersLayer.addLayer(marker);
            }});

            document.getElementById('totalVisibleCount').innerText = visibleCount;
        }}

        // 3. Render Floating Legend
        function renderLegend() {{
            const container = document.getElementById('legendItemsList');
            container.innerHTML = '';
            summaryStats.forEach(item => {{
                const div = document.createElement('div');
                div.className = 'legend-item';
                div.innerHTML = `
                    <span class="legend-color" style="background:${{item.color}}"></span>
                    <span>${{item.name}} (${{item.geocoded}}處)</span>
                `;
                container.appendChild(div);
            }});
        }}

        // 4. Render Origin Group Chips
        function renderChips() {{
            const container = document.getElementById('chipsContainer');
            container.innerHTML = '';
            summaryStats.forEach(item => {{
                const chip = document.createElement('button');
                const isActive = activeOrigins.has(item.name);
                chip.className = `chip ${{isActive ? 'active' : ''}}`;
                chip.style.borderColor = isActive ? item.color : '#cbd5e1';
                chip.innerHTML = `
                    <span class="chip-dot" style="background:${{item.color}}"></span>
                    <span>${{item.name}}</span>
                    <span class="chip-count">(${{item.geocoded}})</span>
                `;
                chip.onclick = () => toggleOrigin(item.name);
                container.appendChild(chip);
            }});
        }}

        // 5. Toggle Origin filter
        function toggleOrigin(name) {{
            if (activeOrigins.has(name)) {{
                if (activeOrigins.size > 1) {{
                    activeOrigins.delete(name);
                }} else {{
                    // If clicking the only active, restore all
                    activeOrigins = new Set(summaryStats.map(s => s.name));
                }}
            }} else {{
                activeOrigins.add(name);
            }}
            renderChips();
            renderMarkers();
            filterSites();
        }}

        function resetFilters() {{
            activeOrigins = new Set(summaryStats.map(s => s.name));
            if (document.getElementById('searchInput')) {{
                document.getElementById('searchInput').value = '';
            }}
            renderChips();
            renderMarkers();
            filterSites();
        }}

        // 6. Render Sites in Sidebar List
        function renderSitesList(items) {{
            const container = document.getElementById('sitesList');
            container.innerHTML = '';
            if (items.length === 0) {{
                container.innerHTML = '<div style="padding:24px; text-align:center; color:#94a3b8; font-size:13px;">查無相符會館組織</div>';
                return;
            }}

            items.forEach(site => {{
                const card = document.createElement('div');
                card.className = 'site-card';
                card.innerHTML = `
                    <div class="site-card-top">
                        <span class="site-card-name">${{site.nameZh}}</span>
                        <span class="site-card-tag" style="background:${{site.color}}">${{site.origin}}</span>
                    </div>
                    <div class="site-card-sub">${{site.nameAlt}}</div>
                    <div class="site-card-foot">
                        <span>最早銘刻: ${{site.dateISO || '未詳'}}</span>
                        <span class="${{site.hasCoord ? 'badge-mapped' : 'badge-unmapped'}}">
                            ${{site.hasCoord ? '● 已在地圖標註' : '○ 無座標'}}
                        </span>
                    </div>
                `;

                card.onclick = () => {{
                    if (site.hasCoord && map) {{
                        map.flyTo([site.lat, site.lng], 15, {{ duration: 1.2 }});
                        // Find marker and open popup
                        markersLayer.eachLayer(layer => {{
                            if (layer.getLatLng && layer.getLatLng().lat === site.lat && layer.getLatLng().lng === site.lng) {{
                                layer.openPopup();
                            }}
                        }});
                        // Close sidebar on mobile
                        if (window.innerWidth <= 768) {{
                            toggleSidebar(false);
                        }}
                    }} else {{
                        alert(`${{site.nameZh}} (${{site.origin}}) 在原書中記錄但暫無現代座標。\\n地址: ${{site.address || '無'}}`);
                    }}
                }};

                container.appendChild(card);
            }});
        }}

        // 7. Filter Sites based on search & active origins
        function filterSites() {{
            const q = document.getElementById('searchInput').value.trim().toLowerCase();
            const filtered = pointsData.filter(site => {{
                const matchOrigin = activeOrigins.has(site.origin);
                const matchSearch = !q || (
                    site.nameZh.toLowerCase().includes(q) ||
                    site.nameAlt.toLowerCase().includes(q) ||
                    site.origin.toLowerCase().includes(q) ||
                    (site.dateISO && site.dateISO.toLowerCase().includes(q)) ||
                    (site.address && site.address.toLowerCase().includes(q))
                );
                return matchOrigin && matchSearch;
            }});

            renderSitesList(filtered);
            renderMarkers();
        }}

        // 8. Toggle Sidebar on Mobile
        function toggleSidebar(forceState) {{
            const sidebar = document.getElementById('sidebar');
            if (forceState !== undefined) {{
                if (forceState) sidebar.classList.add('mobile-open');
                else sidebar.classList.remove('mobile-open');
            }} else {{
                sidebar.classList.toggle('mobile-open');
            }}
        }}

        window.addEventListener('DOMContentLoaded', initMap);
    </script>
</body>
</html>
"""

# Write to immigrant_map.html
with open(output_map_html, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Generated standalone map at: {output_map_html}")

# Also write to index.html so visiting root loads the map directly, or update index.html
with open(output_index_html, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Updated index.html to load the map dashboard by default at: {output_index_html}")
