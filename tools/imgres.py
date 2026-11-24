"""Bildauflösung (kürzere Seite in Pixeln) aller Uhrenbilder in modelle.json unter "imgRes" eintragen.
Die Startseite wählt Uhr/Artikel des Tages bevorzugt aus Modellen mit hochauflösendem Bild (Hauptbild oder Variante)."""
import json,re,os
from PIL import Image
os.chdir(os.path.join(os.path.dirname(__file__),'..'))
d=json.load(open('modelle.json'))
res={}
for p in sorted(set(re.findall(r'assets/watches/[^"]+?\.(?:jpg|jpeg|png|webp)',json.dumps(d['modelle'])))):
    try: res[p.split('/')[-1]]=min(Image.open(p).size)
    except OSError: pass
d['imgRes']=res
json.dump(d,open('modelle.json','w'),ensure_ascii=False,indent=1)
print(len(res),'Bilder,',sum(v>=600 for v in res.values()),'ab 600 px')
