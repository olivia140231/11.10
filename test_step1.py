import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv(r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv')

keywords_step1_candidates = ['會館', '公所', '同鄉會', '同鄉', '公會', '公司', '俱樂部']

for kw in keywords_step1_candidates:
    matches = df[df['siteNameZh'].fillna('').str.contains(kw)]
    print(f'Keyword: "{kw}" -> {len(matches)} matches')

print("\n--- Rows with '公會' ---")
for s in df[df['siteNameZh'].fillna('').str.contains('公會')]['siteNameZh']:
    print(s)

print("\n--- Rows with '公司' ---")
for s in df[df['siteNameZh'].fillna('').str.contains('公司')]['siteNameZh']:
    print(s)

print("\n--- Rows with '俱樂部' ---")
for s in df[df['siteNameZh'].fillna('').str.contains('俱樂部')]['siteNameZh']:
    print(s)
