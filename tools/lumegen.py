"""Leuchtebene je Uhr: helle Flächen (Indizes, Zeiger) innerhalb des Zifferblatts, Ausschlüsse je Uhr."""
import json,sys,numpy as np
from PIL import Image,ImageFilter
from collections import deque
ROOT='/home/user/WikiTicks/'
def comps(mask):
    h,w=mask.shape;lab=np.zeros((h,w),np.int32);out=[];n=0
    ys,xs=np.nonzero(mask)
    for y0,x0 in zip(ys,xs):
        if lab[y0,x0]:continue
        n+=1;q=deque([(y0,x0)]);lab[y0,x0]=n;pts=[]
        while q:
            y,x=q.popleft();pts.append((y,x))
            for dy,dx in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                yy,xx=y+dy,x+dx
                if 0<=yy<h and 0<=xx<w and mask[yy,xx] and not lab[yy,xx]: lab[yy,xx]=n;q.append((yy,xx))
        out.append(np.array(pts))
    return out
def gen(img, spec):
    im=Image.open(ROOT+img).convert('RGB');a=np.array(im).astype(int);h,w,_=a.shape
    L=a.mean(2);S=a.max(2)-a.min(2)
    cx,cy,r=spec['c'][0]*w,spec['c'][1]*h,spec['r']*w
    yy,xx=np.mgrid[0:h,0:w];inside=np.hypot(xx-cx,yy-cy)<=r
    m=inside&(L>=spec.get('thr',175))&(S<=spec.get('sat',70))
    for x0,y0,x1,y1 in spec.get('ex',[]): m[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]=False
    k=spec.get('open',0)
    if k: m=np.array(Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k)))>127
    keep=np.zeros((h,w),bool);minA=spec.get('min',.0004)*w*w
    for c in comps(m):
        if len(c)<minA: continue
        y0,x0=c.min(0);y1,x1=c.max(0)
        sub=np.zeros((y1-y0+3,x1-x0+3),bool);sub[c[:,0]-y0+1,c[:,1]-x0+1]=True
        # Löcher füllen: alles, was vom Rand aus nicht erreichbar ist, gehört zur Fläche
        out=np.zeros_like(sub);q=deque([(0,0)]);out[0,0]=True;H2,W2=sub.shape
        while q:
            y,x=q.popleft()
            for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
                yy,xx=y+dy,x+dx
                if 0<=yy<H2 and 0<=xx<W2 and not sub[yy,xx] and not out[yy,xx]: out[yy,xx]=True;q.append((yy,xx))
        fill=~out
        ys2,xs2=np.nonzero(fill);keep[ys2+y0-1,xs2+x0-1]=True
    for x0,y0,x1,y1 in spec.get('add',[]): # zusätzlich zu übernehmende Bereiche (alles Helle darin)
        sub=(L>=spec.get('thr',175)-40)&(S<=spec.get('sat',70)+10);keep[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]|=sub[int(y0*h):int(y1*h),int(x0*w):int(x1*w)]
    # Kanten glätten
    mk=Image.fromarray((keep*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.7))
    col=(185,232,255) if spec.get('col','g')=='b' else (175,255,205)
    ov=Image.new('RGBA',(w,h),col+(0,));ov.putalpha(mk)
    # auf max. 900 px Höhe verkleinern
    if h>900: ov=ov.resize((round(w*900/h),900),Image.LANCZOS)
    return ov,keep
if __name__=='__main__':
    specs=json.load(open(sys.argv[1]))
    for img,spec in specs.items():
        ov,keep=gen(img,spec)
        name=img.split('/')[-1].rsplit('.',1)[0]+'.png'
        ov.save(ROOT+'assets/watches/lume/'+name,optimize=True)
        # Vorschau
        base=Image.open(ROOT+img).convert('RGB');pv=base.point(lambda v:int(v*.35)).convert('RGBA')
        pv.alpha_composite(ov.resize(base.size));pv.convert('RGB').save('/tmp/pv_'+name)
        print(name,int(keep.sum()))
