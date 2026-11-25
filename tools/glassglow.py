"""Leichter Lichtschein vom Glasrand nach innen in die Leuchtmasken-PNGs einrechnen (Rolex).
Glasrand = Innenkante der Lünette: Kreis an die Gehäusekante (wie imgfit) × modellabhängiger Faktor.
Aufruf: python3 tools/glassglow.py [--check]  (--check: nur Kontrollbild mit Kreisen)"""
import json,sys,os,subprocess
import numpy as np
from PIL import Image,ImageDraw
os.chdir(os.path.join(os.path.dirname(__file__),'..'))
RATIO={"submariner":.755,"sea-dweller":.755,"deepsea":.735,"gmt-master":.76,"explorer-2":.80,"daytona":.78,"yacht-master":.725,
 "yacht-master-ii":.74,"sky-dweller":.80,"datejust":.80,"day-date":.80,"land-dweller":.80,"explorer":.86,"air-king":.86,
 "milgauss":.87,"oyster-perpetual":.87,"perpetual-1908":.87,"oysterquartz":.80}
STRENGTH,WIDTH=38,.10
def circle(path):
  """Mitte: Achse des Bandes (Mitte oben/unten) und Höhe der breitesten Stelle des Gehäuses; Radius bis zur linken Gehäusekante."""
  A=np.asarray(Image.open(path).convert('RGB')).astype(int);H,W,_=A.shape
  fg=(A.min(2)<232)|((A.max(2)-A.min(2))>18)
  def mid(r0,r1):
    xs=[(np.nonzero(fg[y])[0].min()+np.nonzero(fg[y])[0].max())/2 for y in range(int(H*r0),int(H*r1)) if fg[y].sum()>W*.05]
    return float(np.median(xs)) if xs else W/2
  ax=(mid(.03,.12)+mid(.88,.97))/2
  L=[(np.nonzero(fg[y])[0].min(),y) for y in range(int(H*.3),int(H*.7)) if fg[y].any()]
  xmin=min(l for l,_ in L);ys=[y for l,y in L if l<=xmin+2];cy=float(np.median(ys))
  return ax,cy,ax-xmin,W,H
M=json.load(open('modelle.json'));L=M['lumeMasks']
jobs=[]
for m in M['modelle']:
  if m.get('brand')!='Rolex' or m['id'] not in RATIO: continue
  imgs=[m['v'].get('img')]+[(v.get('v') or {}).get('img') for v in m.get('var',[])]+[(m.get('topv') or {}).get('v',{}).get('img')]
  for img in filter(None,set(imgs)):
    f=img.split('/')[-1]
    if L.get(f)!='b': continue   # nur blaue Leuchtmasse (Chromalight)
    jobs.append((m['id'],img,f))
if '--check' in sys.argv:
  tiles=[]
  for mid,img,f in jobs:
    cx,cy,r,W,H=circle(img);im=Image.open(img).convert('RGB');d=ImageDraw.Draw(im);R=r*RATIO[mid]
    d.ellipse([cx-R,cy-R,cx+R,cy+R],outline=(255,0,0),width=max(2,int(W/250)))
    t=im.crop((int(cx-r*1.05),int(cy-r*1.05),int(cx+r*1.05),int(cy+r*1.05))).resize((220,220));ImageDraw.Draw(t).text((3,3),f[6:30],fill=(0,0,255));tiles.append(t)
  cols=8;rows=(len(tiles)+cols-1)//cols;c=Image.new('RGB',(cols*225,rows*225),'gray')
  for i,t in enumerate(tiles): c.paste(t,((i%cols)*225,(i//cols)*225))
  c.save(sys.argv[sys.argv.index('--check')+1]);print(len(tiles));sys.exit()
for mid,img,f in jobs:
  p='assets/watches/lume/'+f.rsplit('.',1)[0]+'.png'
  orig=subprocess.run(['git','show','HEAD~1:'+p] if f=='rolex-submariner-126610ln.jpg' else ['git','show','HEAD:'+p],capture_output=True).stdout
  import io;m_=Image.open(io.BytesIO(orig)).convert('RGBA');mw,mh=m_.size
  cx,cy,r,W,H=circle(img);s=mw/W;R=r*RATIO[mid]*s;c=(cx*s,cy*s)
  yy,xx=np.mgrid[0:mh,0:mw];d=np.hypot(xx-c[0],yy-c[1]);t=np.clip((R-d)/(R*WIDTH),0,None)
  g=np.where(d<=R,np.clip(1-t,0,1)**2,0.0)
  A=np.asarray(m_).copy()
  if A[:,:,3].max()==0: continue
  col=A[A[:,:,3]>200][:,:3].mean(0).astype(np.uint8)
  ga=(g*STRENGTH).astype(np.uint8);hit=ga>A[:,:,3]
  A[hit,0],A[hit,1],A[hit,2]=col[0],col[1],col[2];A[:,:,3]=np.maximum(A[:,:,3],ga)
  Image.fromarray(A).save(p,optimize=True);print(mid,f)
