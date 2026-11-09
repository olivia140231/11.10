import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv(r'c:\Users\James Lin\Desktop\21205\01-franke_malaysia.csv')

step1_kws = ['會館', '公所', '同鄉會', '公會']
pattern1 = '|'.join(step1_kws)
df_step1 = df[df['siteNameZh'].fillna('').str.contains(pattern1)].copy()

# Let's test if there is any record among the 81 not covered
all_kws = [
    '瓊州', '琼州', '海南',
    '廣肇', '番禺', '會寗', '台山', '寧陽', '岡州', '四邑', '南海', '香山', '中山', '順德', '清遠', '東安', '增龍',
    '福建', '安溪', '永春', '漳泉', '漳州', '泉州', '惠安', '晉江', '同安', '金厦', '興安', '閩南', '詔安', '福州', '龍巖',
    '惠州', '鵝城', '嘉應', '應和', '茶陽', '大埔', '海陸', '客屬', '永定',
    '潮州', '韓江',
    '廣西',
    '雷州',
    '廣東會館', '廣東暨汀州', '平章會館', '古城會館',
    '商業職員公會'
]

pattern_all = '|'.join(all_kws)
uncovered = df_step1[~df_step1['siteNameZh'].str.contains(pattern_all)]
print("Uncovered count:", len(uncovered))
if len(uncovered) > 0:
    print(uncovered[['nanyangSiteId', 'siteNameZh']])
else:
    print("100% of the 81 records are successfully matched and accounted for!")
