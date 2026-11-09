import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv(r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv')

# Step 1: Filter immigrant associations
step1_kws = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(step1_kws)
df_step1 = df[df['siteNameZh'].fillna('').str.contains(pattern1)].copy()
print(f"【步驟一】利用第一組關鍵字 {step1_kws} 篩選出: {len(df_step1)} 筆")

# Step 2: Define Origin Keywords & Classify
# We classify into major ancestral origin groups (按方言群/原籍地):
groups = {
    '海南群 (瓊州)': ['瓊州', '琼州', '海南'],
    '廣府群 (粵語廣肇/四邑/珠三角)': ['廣肇', '番禺', '會寗', '台山', '寧陽', '岡州', '四邑', '南海', '香山', '中山', '順德', '清遠', '東安', '增龍'],
    '閩籍 / 閩南群 (福建各府縣)': ['福建', '安溪', '永春', '漳泉', '漳州', '泉州', '惠安', '晉江', '同安', '金厦', '興安', '閩南', '詔安', '福州', '龍巖'],
    '客家群 (客屬/粵東閩西客籍)': ['惠州', '鵝城', '嘉應', '應和', '茶陽', '大埔', '海陸', '客屬', '永定'],
    '潮州群 (潮汕/韓江)': ['潮州', '韓江'],
    '廣西群': ['廣西'],
    '雷州群': ['雷州'],
    '跨省/總合華人機構': ['廣東會館', '廣東暨汀州', '廣肇惠', '平章會館', '古城會館'],
    '其他非地緣公會': ['商業職員公會']
}

print("\n【步驟二】各大原籍分類篩選統計：")
categorized_counts = {}
assigned_sites = set()

for grp_name, kws in groups.items():
    pattern = '|'.join(kws)
    # Check in siteNameZh
    matched = df_step1[df_step1['siteNameZh'].str.contains(pattern)]
    print(f"\n▶ {grp_name}（關鍵字：{kws}）-> 篩出 {len(matched)} 筆:")
    for name in matched['siteNameZh']:
        print(f"   - {name}")
    categorized_counts[grp_name] = len(matched)
