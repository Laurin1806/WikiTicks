"""Geometrische Leuchtmaske: Indexstreifen rund um die Mitte + Zeigerstreifen (Richtung per Strahlabtastung)."""
import json,sys,math,numpy as np
from PIL import Image,ImageDraw,ImageFilter
import os;ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/';D='/tmp/'
def hand_angles(L,hub,R,n=2,excl=()):
    hx,hy=hub;sc=[]
    for a in range(0,360):
        t=math.radians(a);vals=[]
        for f in np.linspace(.18,.55,40):
            x=int(hx+math.sin(t)*R*f);y=int(hy-math.cos(t)*R*f)
            if 0<=y<L.shape[0] and 0<=x<L.shape[1]: vals.append(L[y,x])
        sc.append(np.std(vals)*-1+abs(np.mean(vals)-np.median(L[int(hy-R*.5):int(hy+R*.5),int(hx-R*.5):int(hx+R*.5)]))*2)
    sc=np.array(sc);sc=np.convolve(np.r_[sc[-3:],sc,sc[:3]],np.ones(7)/7,'same')[3:-3]
    out=[]
    for _ in range(n):
        a=int(np.argmax(sc));out.append(a)
        for d in range(-25,26): sc[(a+d)%360]=-1e9
    return out
def build(img,p):
    im=Image.open(ROOT+img).convert('RGB');W,H=im.size;L=np.asarray(im).astype(float).mean(2)
    hub=p['hub'];R=p['R'];S=[]
    for h in range(12):
        if h in p.get('skip',[]): continue
        a=math.radians(h*30);r0,r1=R*p.get('ri',.74),R*p.get('ro',.9)
        if h==0 and p.get('dbl12'):
            for o in (-1,1): S.append(((hub[0]+o*p['dbl12'],hub[1]-r1),(hub[0]+o*p['dbl12'],hub[1]-r0),p.get('iw',R*.03)))
            continue
        S.append(((hub[0]+math.sin(a)*r0,hub[1]-math.cos(a)*r0),(hub[0]+math.sin(a)*r1,hub[1]-math.cos(a)*r1),p.get('iw',R*.03)))
    hs=p.get('hands') or hand_angles(L,hub,R)
    for k,a in enumerate(hs[:2]):
        ln=R*(p.get('hl',[.5,.78])[k] if isinstance(p.get('hl'),list) else .6);t=math.radians(a)
        S.append(((hub[0]+math.sin(t)*R*.2,hub[1]-math.cos(t)*R*.2),(hub[0]+math.sin(t)*ln,hub[1]-math.cos(t)*ln),p.get('hw',R*.035)))
    m=Image.new('L',(W,H),0);d=ImageDraw.Draw(m)
    for a,b,w in S: d.line([a,b],fill=255,width=max(2,int(w)))
    m=m.filter(ImageFilter.GaussianBlur(.7));al=np.clip((np.asarray(m).astype(float)-40)*255/150,0,255).astype(np.uint8)
    ov=Image.new('RGBA',(W,H),(175,255,205,0));ov.putalpha(Image.fromarray(al))
    if H>900: ov=ov.resize((round(W*900/H),900),Image.LANCZOS)
    n=img.split('/')[-1][:-4];ov.save(D+'out2/'+n+'.png',optimize=True)
    pv=im.point(lambda v:int(v*.35)).convert('RGBA');pv.alpha_composite(ov.resize((W,H)));pv.convert('RGB').save(D+'pv_'+n+'.png')
    return hs
if __name__=='__main__':
    P=json.load(open(sys.argv[1]))
    for img,p in P.items(): print(img.split('/')[-1],build(img,p))
