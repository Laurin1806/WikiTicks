import numpy as np,sys
from PIL import Image,ImageFilter
sys.path.insert(0,'.')
from lumegen import comps
import os;R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','assets','watches')+'/'
def build(name,cand_fn,hub,rad,ex_circ=(),ex_box=(),minpx=40,er=1,col=(175,255,205),fill=False,dots=(),pca=False,strips=()):
  im=Image.open(R+name+'.jpg').convert('RGB');a=np.asarray(im).astype(int);H,W,_=a.shape
  L=a.mean(2);S=a.max(2)-a.min(2);yy,xx=np.mgrid[0:H,0:W]
  m=cand_fn(L,S)&(np.hypot(xx-hub[0],yy-hub[1])<rad)
  for cx,cy,cr in ex_circ: m&=np.hypot(xx-cx,yy-cy)>cr
  for x0,y0,x1,y1 in ex_box: m[y0:y1,x0:x1]=False
  keep=np.zeros_like(m)
  for c in comps(m):
    if len(c)<minpx: continue
    hh=np.ptp(c[:,0])+1;ww=np.ptp(c[:,1])+1
    if max(hh,ww)/max(1,min(hh,ww))<2.2 and len(c)<minpx*3: continue   # Schrift/Punkte
    if pca:   # Rahmen + Leuchtmasse als ein Balken: Achse bestimmen, schmaleren Streifen mittig einzeichnen
      from PIL import ImageDraw
      pts=c[:,::-1].astype(float);mu=pts.mean(0);u,sv,vt=np.linalg.svd(pts-mu,full_matrices=False);ax=vt[0];pe=vt[1]
      pa=(pts-mu)@ax;pb=(pts-mu)@pe;l2=(pa.max()-pa.min())/2*.86;w2=(pb.max()-pb.min())/2*.42;ca=(pa.max()+pa.min())/2;cb=(pb.max()+pb.min())/2
      cen=mu+ca*ax+cb*pe;poly=[tuple(cen+sa*l2*ax+sb*w2*pe) for sa,sb in((-1,-1),(1,-1),(1,1),(-1,1))]
      im2=Image.new('L',(W,H),0);ImageDraw.Draw(im2).polygon(poly,fill=255);keep|=np.asarray(im2)>0
      continue
    if fill:   # Fläche samt Rahmen füllen, dann kräftig einrücken: nur die Innenfläche (Leuchtmasse) bleibt
      y0,x0=c.min(0);sub=np.zeros((hh+2,ww+2),np.uint8);sub[c[:,0]-y0+1,c[:,1]-x0+1]=255
      f=Image.fromarray(sub).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
      e=np.asarray(f.filter(ImageFilter.MinFilter(2*er+1)))>127;ys,xs=np.nonzero(e);keep[ys+y0-1,xs+x0-1]=True
    else: keep[c[:,0],c[:,1]]=True
  for cx,cy,cr in dots: keep|=np.hypot(xx-cx,yy-cy)<=cr
  from PIL import ImageDraw
  for (x0,y0),(x1,y1),wd in strips:   # vorher Automatik-Reste entlang des Streifens entfernen
    im2=Image.new('L',(W,H),0);ImageDraw.Draw(im2).line([(x0,y0),(x1,y1)],fill=255,width=int(wd*2.6));keep&=~(np.asarray(im2)>0)
  for (x0,y0),(x1,y1),wd in strips:
    im2=Image.new('L',(W,H),0);ImageDraw.Draw(im2).line([(x0,y0),(x1,y1)],fill=255,width=int(wd));keep|=np.asarray(im2)>0
  mk=Image.fromarray((keep*255).astype(np.uint8))
  if er and not fill: mk=mk.filter(ImageFilter.MinFilter(2*er+1))
  mk=mk.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.7))
  al=np.asarray(mk).astype(float);al=np.clip((al-40)*255/150,0,255).astype(np.uint8)
  ov=Image.new('RGBA',(W,H),col+(0,));ov.putalpha(Image.fromarray(al))
  if H>900: ov=ov.resize((round(W*900/H),900),Image.LANCZOS)
  ov.save(R+'lume/'+name+'.png',optimize=True)
  o2=im.copy();o2.paste(Image.new('RGB',im.size,(255,0,0)),(0,0),Image.fromarray(al).point(lambda v:int(v*.8)))
  o2.crop((int(W*.15),int(H*.28),int(W*.85),int(H*.72))).save('ov_'+name[-6:]+'.png')
# 5711 weiß: cremefarbene Leuchtmasse (S>=19) auf weißem Zifferblatt (S<12)
build('patek-philippe-nautilus-5711-1a-white',lambda L,S:(S>=19)&(L>=185)&(L<=245),(495,716),300,ex_box=[(690,690,760,760)],minpx=60,er=1)
# 5740: weiße Leuchtmasse in den Indizes, Hilfszifferblätter und Schrift ausgenommen
build('patek-philippe-nautilus-5740-1g-perpetual',lambda L,S:(L>=185)&(S<=50),(469.6,608.4),262,
  ex_circ=[(324,611.6,80),(624,615.6,80),(470.4,762,112),(469.6,608.4,22)],ex_box=[(380,460,570,530),(615,440,710,525)],minpx=40,er=0,pca=True,strips=[((646,505),(693,484),7),((503,583),(666,462),7)],dots=[(219.5,611.5,3.6),(721.5,611.5,3.6)])
