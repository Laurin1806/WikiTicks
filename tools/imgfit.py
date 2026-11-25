"""Bildausrichtung: Uhr in jedem Bild mittig setzen und nach Gehäusedurchmesser skalieren.
Bezug: Submariner 126610LN/124060 (41 mm) in rolex-submariner-126610ln.jpg.
Ergebnis in modelle.json unter "imgFit": {Datei: [Skalierung, Versatz in Bildbreiten]}.
Aufruf: python3 tools/imgfit.py [modell-id ...]   (ohne Angabe: alle Modelle)"""
import json,re,sys,os
import numpy as np
from PIL import Image
os.chdir(os.path.join(os.path.dirname(__file__),'..'))
REF_IMG,REF_MM='rolex-submariner-126610ln.jpg',41.0
def meas(path):
  A=np.asarray(Image.open(path).convert('RGB')).astype(int);H,W,_=A.shape
  fg=(A.min(2)<232)|((A.max(2)-A.min(2))>18)
  def mid(r0,r1):
    xs=[(np.nonzero(fg[y])[0].min()+np.nonzero(fg[y])[0].max())/2 for y in range(int(H*r0),int(H*r1)) if fg[y].sum()>W*.05]
    return float(np.median(xs)) if xs else W/2
  ax=(mid(.03,.12)+mid(.88,.97))/2
  best=0
  for y in range(int(H*.3),int(H*.7)):
    c=np.nonzero(fg[y])[0]
    if len(c): best=max(best,ax-c.min())   # Radius ohne Krone (rechts)
  return 2*best/H,(ax-W/2)/W
mmre=re.compile(r'(\d+(?:,\d+)?)\s*mm')
def mm_of(txt):
  m=mmre.search(txt or '');return float(m.group(1).replace(',','.')) if m else None
M=json.load(open('modelle.json'));D=json.load(open('datenblatt.json'))
ref_frac,_=meas('assets/watches/'+REF_IMG);k=ref_frac/REF_MM
fit=M.get('imgFit',{});ids=set(sys.argv[1:])
for m in M['modelle']:
  if ids and m['id'] not in ids: continue
  base=mm_of((D.get(m['id']) or {}).get('durchmesser'))
  items=[('main',(m.get('topv') or {}).get('v',{}).get('img') or m['v'].get('img'))]+[(str(i),(v.get('v') or {}).get('img')) for i,v in enumerate(m.get('var',[]))]
  for key,img in items:
    if not img: continue
    mm=mm_of((D['_bilder'].get(f"{m['id']}|{key}") or {}).get('durchmesser')) or base
    if not mm or '×' in str((D['_bilder'].get(f"{m['id']}|{key}") or {}).get('durchmesser','')): continue
    f=img.split('/')[-1]
    try: frac,dx=meas(img)
    except Exception as e: print('Fehler',f,e); continue
    shaped=re.search(r'santos|tank|reverso|ellipse|crash|panthere|baignoire|oysterquartz|cle-de|tortue|twenty4|bubbleback|monaco|carree|rectang',f)
    sc=round(max(.72,min(1.0 if shaped else 1.08,k*mm/frac)),3)   # Formuhren werden höchstens zentriert und verkleinert (Breite misst ihr Gehäuse nicht zuverlässig)
    fit[f]=[sc,round(-dx,4)]; print(m['id'],f,mm,'mm  Skala',sc,'Versatz',round(-dx,3))
M['imgFit']=fit
json.dump(M,open('modelle.json','w'),ensure_ascii=False,indent=1)
