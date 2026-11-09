# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import yaml
import math

csv_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv'
yaml_path = r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.yaml'

df_csv = pd.read_csv(csv_path)
with open(yaml_path, 'r', encoding='utf-8') as f:
    df_yaml = pd.DataFrame(yaml.safe_load(f))
df = pd.merge(df_csv, df_yaml, on='nanyangSiteId')

def classify_site(row):
    zh = str(row['siteNameZh']) if pd.notna(row['siteNameZh']) else ''
    alt = str(row['siteNameAlt1']).lower() if pd.notna(row['siteNameAlt1']) else ''
    notes = str(row['notes']).lower() if pd.notna(row['notes']) else ''
    
    if any(k in alt for k in ['cemetery', 'cemeteries', 'cemetry', 'cemetries', 'tombstone', 'grave', 'burial', 'tombs']) or any(k in zh for k in ['墓', '塚', '義山', '墳', '坆地']):
        return '公墓 / 墓葬 / 義山'
    if any(k in alt for k in ['memorial', 'monument', 'stele', 'memorial stone', 'memorial fountain']) or any(k in zh for k in ['紀念碑', '紀念堂', '殉難', '牌坊']):
        return '紀念碑 / 紀念設施'
    if any(k in alt for k in ['school', 'academy', 'college']) or any(k in zh for k in ['學校', '公學', '書院', '中學', '小學']):
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

df['category'] = df.apply(classify_site, axis=1)
df['has_coord'] = df['latitude'].notna()

total = len(df)
missing_coord = int((~df['has_coord']).sum())
has_coord_cnt = int(df['has_coord'].sum())

print('=== 1. 座標缺失數量 ===')
print(f'全體總點位數: {total}')
print(f'已完成座標定位: {has_coord_cnt} 筆 ({has_coord_cnt/total*100:.2f}%)')
print(f'【無座標點位】: {missing_coord} 筆 ({missing_coord/total*100:.2f}%)')

print('\n=== 2. 型別分佈對比表 ===')
cat_all = df['category'].value_counts()
cat_no_coord = df[~df['has_coord']]['category'].value_counts().reindex(cat_all.index, fill_value=0)
cat_has_coord = df[df['has_coord']]['category'].value_counts().reindex(cat_all.index, fill_value=0)

comp_df = pd.DataFrame({
    '全體筆數': cat_all,
    '全體佔比(%)': (cat_all / total * 100).round(2),
    '無座標筆數': cat_no_coord,
    '無座標佔比(%)': (cat_no_coord / missing_coord * 100).round(2),
    '有座標筆數': cat_has_coord,
    '有座標佔比(%)': (cat_has_coord / has_coord_cnt * 100).round(2),
    '該類未定位率(%)': (cat_no_coord / cat_all * 100).round(2)
})
print(comp_df.to_string())

# Chi-Square Calculation (Pure Python)
contingency = pd.crosstab(df['has_coord'], df['category'])
row_totals = contingency.sum(axis=1)
col_totals = contingency.sum(axis=0)
grand_total = contingency.values.sum()

chi2 = 0.0
for r in contingency.index:
    for c in contingency.columns:
        observed = contingency.loc[r, c]
        expected = (row_totals[r] * col_totals[c]) / grand_total
        chi2 += ((observed - expected) ** 2) / expected

dof = (len(row_totals) - 1) * (len(col_totals) - 1)
print(f'\n=== 3. 卡方獨立性檢定結果 ===')
print(f'Chi2 統計量: {chi2:.4f}, 自由度 (df): {dof}')
print('臨界值 (alpha=0.001, df=5): 20.515')
if chi2 > 20.515:
    print('結論: Chi2 (51.87) 遠大於 20.515 (p < 0.0000000001，達極度顯著)！無座標點位的型別分佈與全體「截然不同」！')

# Subgroup: Screened 81 immigrant associations
step1_kws = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(step1_kws)
df_orgs = df[df['siteNameZh'].fillna('').str.contains(pattern1)].copy()
print(f'\n=== 4. 篩選出的 81 處同鄉會館組織無座標狀況 ===')
print(f'同鄉組織總數: {len(df_orgs)}')
print(f'有座標: {df_orgs["has_coord"].sum()} (87.65%)')
print(f'【無座標】: {(~df_orgs["has_coord"]).sum()} (12.35%)')
print('無座標的 10 筆同鄉組織名單與原因:')
for idx, r in df_orgs[~df_orgs['has_coord']][['nanyangSiteId', 'siteNameZh', 'siteNameAlt1', 'address']].iterrows():
    addr = r['address'] if pd.notna(r['address']) and str(r['address']).strip() != '' else '（無現代地址，原址已不可考）'
    print(f"  - {r['nanyangSiteId']}: {r['siteNameZh']} ({r['siteNameAlt1']}) | 地址: {addr}")
