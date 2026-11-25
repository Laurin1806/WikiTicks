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
  """Kreis an die linke Gehäusekante (Lünettenbogen) anpassen: Durchmesser als Anteil der Bildhöhe und Versatz der Mitte.
  Links, weil rechts die Krone sitzt; Ausreißer (Heliumventil, Bandanstöße) werden schrittweise entfernt."""
  A=np.asarray(Image.open(path).convert('RGB')).astype(int);H,W,_=A.shape
  fg=(A.min(2)<232)|((A.max(2)-A.min(2))>18)
  pts=[(np.nonzero(fg[y])[0].min(),y) for y in range(int(H*.25),int(H*.75)) if fg[y].any()]
  P=np.array(pts,float);x,y=P[:,0],P[:,1]
  def circ(x,y):
    M=np.c_[x,y,np.ones_like(x)];D,E,F=np.linalg.lstsq(M,-(x**2+y**2),rcond=None)[0];cx,cy=-D/2,-E/2;return cx,cy,np.sqrt(max(1,cx**2+cy**2-F))
  sel=np.abs(y-y[np.argmin(x)])<H*.13
  for _ in range(4):
    cx,cy,r=circ(x[sel],y[sel]);res=np.abs(np.hypot(x-cx,y-cy)-r);sel=sel&(res<max(2,np.percentile(res[sel],80)))
  # einfache Messung zum Abgleich: Achse aus der Mitte des Bandes oben/unten, Radius bis zur linken Kante
  def mid(r0,r1):
    xs=[(np.nonzero(fg[yy])[0].min()+np.nonzero(fg[yy])[0].max())/2 for yy in range(int(H*r0),int(H*r1)) if fg[yy].sum()>W*.05]
    return float(np.median(xs)) if xs else W/2
  ax=(mid(.03,.12)+mid(.88,.97))/2;rs=ax-x.min()
  # Kreis nur, wenn er zur einfachen Messung passt (runde Gehäuse); sonst (achteckig, Kissen, eckig) die einfache Messung
  if W*.25<cx<W*.75 and abs(r-rs)/rs<.06: return 2*r/H,(cx-W/2)/W
  return 2*rs/H,(ax-W/2)/W
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
