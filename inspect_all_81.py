import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv(r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv')

# Step 1
kws1 = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(kws1)
df_step1 = df[df['siteNameZh'].fillna('').str.contains(pattern1)].copy()

print(f"Step 1 filtered: {len(df_step1)} records")

# Let's inspect each record's siteNameZh and siteNameAlt1
for idx, r in df_step1.iterrows():
    name = r['siteNameZh']
    alt = r['siteNameAlt1']
    print(f"{r['nanyangSiteId']}: {name} ({alt})")
