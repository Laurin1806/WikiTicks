"""Leuchtmasken korrigieren. Je Bild eine Datei tools/lume-fix/<bildname>.json mit einer Liste von Operationen
(Koordinaten in Pixeln des ORIGINAL-Uhrenbilds assets/watches/<bildname>.jpg):
  ["erase_rect", x0, y0, x1, y1]          Bereich löschen
  ["erase_circle", x, y, r]               Kreis löschen
  ["erase_poly", [[x,y],...]]             Vieleck löschen
  ["line", x0, y0, x1, y1, w]             Leuchtstreifen (Index, Zeigerfüllung) mit Breite w
  ["dot", x, y, r]                        runder Leuchtpunkt
  ["poly", [[x,y],...]]                   Leuchtfläche als Vieleck (z. B. Dreieck bei 12)
  ["sel", x0, y0, x1, y1, lmin]           helle, farbarme Pixel im Rechteck als Leuchtmasse (lmin = Mindesthelligkeit 0–255)
Basis ist immer die Maske aus Commit 15f089433e098856be988d468bb4c53e8b6cce6c (so lassen sich Korrekturen beliebig oft neu anwenden).
Aufruf: python3 tools/lumefix.py <bildname> [...]   oder ohne Argument: alle Dateien in tools/lume-fix
Vorschau: python3 tools/lumefix.py --preview <bildname> <ausgabe.png> [cx cy halb]"""
import json,sys,os,io,subprocess,glob
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
os.chdir(os.path.join(os.path.dirname(__file__),'..'))
BASE="15f089433e098856be988d468bb4c53e8b6cce6c"
def base_mask(n):
  b=subprocess.run(['git','show',f'{BASE}:assets/watches/lume/{n}.png'],capture_output=True).stdout
  return Image.open(io.BytesIO(b)).convert('RGBA')
def apply(n):
  ops=json.load(open(f'tools/lume-fix/{n}.json'))
  m=base_mask(n);mw,mh=m.size;im=Image.open(f'assets/watches/{n}.jpg').convert('RGB');W,H=im.size;s=mw/W
  A=np.asarray(m).copy();col=A[A[:,:,3]>200][:,:3].mean(0) if (A[:,:,3]>200).any() else np.array([175,255,205])
  al=Image.fromarray(A[:,:,3]);
  SS=4;big=al.resize((mw*SS,mh*SS));d=ImageDraw.Draw(big);P=lambda x,y:(x*s*SS,y*s*SS)
  for op in ops:
    k=op[0]
    if k=='erase_rect': d.rectangle([P(op[1],op[2]),P(op[3],op[4])],fill=0)
    elif k=='erase_circle': x,y,r=op[1:4];d.ellipse([P(x-r,y-r),P(x+r,y+r)],fill=0)
    elif k=='erase_poly': d.polygon([P(*p) for p in op[1]],fill=0)
    elif k=='line':
      x0,y0,x1,y1,w=op[1:6];d.line([P(x0,y0),P(x1,y1)],fill=255,width=max(2,int(w*s*SS)))
      for x,y in ((x0,y0),(x1,y1)): d.ellipse([P(x-w/2,y-w/2),P(x+w/2,y+w/2)],fill=255)
    elif k=='dot': x,y,r=op[1:4];d.ellipse([P(x-r,y-r),P(x+r,y+r)],fill=255)
    elif k=='poly': d.polygon([P(*p) for p in op[1]],fill=255)
    elif k=='sel':
      x0,y0,x1,y1,lmin=op[1:6];a=np.asarray(im).astype(int)[int(y0):int(y1),int(x0):int(x1)];L=a.mean(2);sat=a.max(2)-a.min(2)
      sm=((L>=lmin)&(sat<40)).astype(np.uint8)*255;smi=Image.fromarray(sm).resize((int((x1-x0)*s*SS),int((y1-y0)*s*SS)))
      bb=np.asarray(big).copy();X0,Y0=int(x0*s*SS),int(y0*s*SS);h,w=bb[Y0:Y0+smi.height,X0:X0+smi.width].shape
      bb[Y0:Y0+h,X0:X0+w]=np.maximum(bb[Y0:Y0+h,X0:X0+w],np.asarray(smi)[:h,:w]);big=Image.fromarray(bb);d=ImageDraw.Draw(big)
  al=big.resize((mw,mh),Image.LANCZOS)
  A[:,:,3]=np.asarray(al);A[:,:,0],A[:,:,1],A[:,:,2]=[int(v) for v in col]
  Image.fromarray(A).save(f'assets/watches/lume/{n}.png',optimize=True)
def preview(n,out,cx=None,cy=None,hf=None):
  im=Image.open(f'assets/watches/{n}.jpg').convert('RGB');W,H=im.size
  m=Image.open(f'assets/watches/lume/{n}.png').getchannel('A').resize((W,H))
  o=Image.composite(Image.new('RGB',(W,H),(255,0,40)),im.point(lambda v:int(v*.55)),m.point(lambda v:int(v*.85)))
  if cx is None: cx,cy,hf=W//2,int(H*.47),int(min(W,H)*.38)
  x0,y0=max(0,cx-hf),max(0,cy-hf);a=o.crop((x0,y0,min(W,cx+hf),min(H,cy+hf)));b=im.crop((x0,y0,min(W,cx+hf),min(H,cy+hf)))
  sc=620/max(a.size);a=a.resize((int(a.width*sc),int(a.height*sc)));b=b.resize(a.size)
  c=Image.new('RGB',(a.width*2+10,a.height),'gray');c.paste(a,(0,0));c.paste(b,(a.width+10,0));d=ImageDraw.Draw(c)
  step=20 if hf<150 else 40 if hf<350 else 80
  for v in range((x0//step+1)*step,x0+2*hf,step):
    X=(v-x0)*sc
    for off in (0,a.width+10): d.line([(X+off,0),(X+off,10 if v%(2*step) else 18)],fill=(0,220,255))
    if v%(2*step)==0: d.text((X+2,18),str(v),fill=(0,220,255))
  for v in range((y0//step+1)*step,y0+2*hf,step):
    Y=(v-y0)*sc
    for off in (0,a.width+10): d.line([(off,Y),(off+(10 if v%(2*step) else 18),Y)],fill=(0,220,255))
    if v%(2*step)==0: d.text((20,Y+2),str(v),fill=(0,220,255))
  c.save(out);print(n,W,H)
if __name__=='__main__':
  a=sys.argv[1:]
  if a and a[0]=='--preview': preview(a[1],a[2],*map(int,a[3:6])) if len(a)>5 else preview(a[1],a[2]);sys.exit()
  names=a or [os.path.basename(p)[:-5] for p in glob.glob('tools/lume-fix/*.json')]
  for n in names: apply(n);print('ok',n)
