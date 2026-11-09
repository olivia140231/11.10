import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv(r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv')

kws1 = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(kws1)

matches1 = df[df['siteNameZh'].fillna('').str.contains(pattern1)]
print(f'Total matches for Step 1 ({kws1}): {len(matches1)}')
print("\nAll matches in Step 1:")
for idx, r in matches1[['nanyangSiteId', 'siteNameZh']].iterrows():
    print(f"{r['nanyangSiteId']}: {r['siteNameZh']}")
